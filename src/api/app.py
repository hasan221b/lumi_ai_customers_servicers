from src.models.load_models import ModelLoader
from src.processing.data_loader import DataLoader
from src.processing.data_embedder import DataEmbedder
from src.processing.data_index import FaissIndex
from src.rag.retriever import Retriever
from src.rag.answer_generator import AnswerGenerator
from src.utils.setting import Query
from src.database.db import get_db_connection, cleanup_old_chats
from fastapi import FastAPI, HTTPException, Response, Request
from src.utils.logger import app_logger
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse 
from pathlib import Path
import uuid
from datetime import datetime, timedelta
from langchain.memory import ConversationSummaryMemory

class ChatbotAPI:
    def __init__(self):
        app_logger.info('Starting the app initialization...')
        
        # Initialize models
        app_logger.info('Initialize models...')
        self.model_loader = ModelLoader()
        self.embedding_model = self.model_loader.embedding_model
        self.llm_model = self.model_loader.get_llm_model()
        self.sentiment_analyzer = self.model_loader.get_sentiment_model()
        self.zero_shot_model = self.model_loader.zero_shot_model()
        app_logger.info('Models initialized successfully')

        # Process data
        app_logger.info('Processing data...')
        self.df = DataLoader().load_data()
        self.embed_df = DataEmbedder(self.embedding_model, self.df).embed_data()
        self.index = FaissIndex(self.df).data_index()
        app_logger.info('Data processing completed successfully')

        # Initialize RAG components
        app_logger.info('Initializing RAG components...')
        self.retriever = Retriever(self.embedding_model, self.index, self.df)
        self.answer_generator = AnswerGenerator(self.llm_model, self.retriever, self.sentiment_analyzer, self.zero_shot_model)
        app_logger.info('RAG components initialized successfully')
        
        # Dictionary to store memory per chat_id
        self.chat_memories = {}

        # Create FastAPI app
        app_logger.info('Initialize API...')
        self.app = FastAPI()

        # Serve static files (frontend)
        app_logger.info('Serving static files...')
        frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
        self.app.mount("/static", StaticFiles(directory=frontend_path, html=True), name="frontend")

        # Enable CORS
        app_logger.info('Enabling CORS...')
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
        cleanup_old_chats()
    def _check_user_limits(self, user_id):
        '''Check if the user has reached their usage limits and handle lockouts'''

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT chats_created, messages_sent, lockout_until FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")
        chats_created = user['chats_created']
        messages_sent = user['messages_sent']
        lockout_until = user['lockout_until']
        current_time = datetime.now()

        # Check if user is currently locked out
        if lockout_until:
            lockout_time = datetime.fromisoformat(lockout_until)
            if current_time < lockout_time:
                remaining_time = (lockout_time - current_time).total_seconds()
                hours_left = int(remaining_time // 3600)
                minutes_left = int((remaining_time % 3600) // 60)
                conn.close()
                raise HTTPException(
                    status_code=403,
                    detail=f"Usage limit reached. Please wait {hours_left}h {minutes_left}m before starting a new chat or sending messages."
                )
            else:
                # Lockout period has expired; reset counters
                cursor.execute(
                    "UPDATE users SET chats_created = 0, messages_sent = 0, lockout_until = NULL WHERE user_id = ?",
                    (user_id,)
                )
                chats_created = 0
                messages_sent = 0
                conn.commit()

        # Check total usage limits
        max_chats = 2
        max_messages_per_chat = 5
        max_total_messages = max_chats * max_messages_per_chat

        if chats_created >= max_chats and messages_sent >= max_total_messages:
            #User has reached the limit; set a 24-hour lockout
            lockout_until = current_time + timedelta(hours=24)
            cursor.execute(
                'UPDATE users SET lockout_until = ? WHERE user_id = ?',(lockout_until.isoformat(), user_id)
                            )
            conn.commit()
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="Usage limit reached. Please wait 24 hours before starting a new chat or sending messages."
            )

        conn.close()
        return chats_created, messages_sent
    
    def _get_or_create_memory(self, chat_id):
        """Get or create a memory instance for a specific chat_id."""
        if chat_id not in self.chat_memories:
            # Always create a fresh memory instance for a new chat
            self.chat_memories[chat_id] = ConversationSummaryMemory(llm=self.llm_model)
            # Clear any existing buffer to ensure independence
            self.chat_memories[chat_id].clear()
        return self.chat_memories[chat_id]

    def _setup_routes(self):
        @self.app.get('/')
        async def read_root():
            app_logger.info('Root endpoint accessed')
            frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
            return FileResponse(frontend_path / "index.html")
        
        @self.app.get('/health')
        async def health_check():
            app_logger.info('Health check endpoint accessed.')
            return {'status': 'healthy'}
        
        @self.app.get('/get_user_id')
        async def get_user_id(request: Request, response: Response):
            user_id = request.cookies.get('user_id')
            if not user_id:
                user_id = str(uuid.uuid4())
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (user_id, created_at, chats_created, messages_sent, lockout_until) VALUES (?, ?, ?, ?, ?)",
                    (user_id, datetime.now(), 0, 0, None)
                )
                conn.commit()
                conn.close()
                response.set_cookie(key='user_id', value=user_id, httponly=True, max_age=604800)
            return {'user_id': user_id}
        
        @self.app.get('/chats/{user_id}')
        async def get_chats(user_id: str):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT chat_id, chat_name FROM chats WHERE user_id = ?", (user_id,))
            chats = cursor.fetchall()
            conn.close()
            return {'chats': [{'chat_id': chat['chat_id'], 'chat_name': chat['chat_name']} for chat in chats]}
        
        @self.app.post('/start_chat/{user_id}')
        async def start_chat(user_id: str):
            chats_created, _ = self._check_user_limits(user_id)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chats WHERE user_id = ?", (user_id,))
            chat_count = cursor.fetchone()[0]
            if chat_count >= 2:
                conn.close()
                app_logger.error("Maximum number of active chats (2) reached for user_id: %s", user_id)
                raise HTTPException(status_code=403, detail="Maximum number of chats (5) reached")
            
            # Increment chats_created
            cursor.execute(
                "UPDATE users SET chats_created = chats_created + 1 WHERE user_id = ?",
                (user_id,)
            )
            chat_name = f"Chat {chat_count + 1}"
            cursor.execute("INSERT INTO chats (user_id, chat_name, summary, created_at, last_updated) VALUES (?, ?, ?, ?, ?)",
                        (user_id, chat_name, "", datetime.now(), datetime.now()))
            chat_id = cursor.lastrowid
            
            # Insert a starter message
            starter_message = "Hello! I'm Lumi, your e-commerce assistant. How can I help you today?"
            cursor.execute("INSERT INTO messages (chat_id, message_type, message_text, timestamp) VALUES (?, ?, ?, ?)",
                        (chat_id, "received", starter_message, datetime.now()))
            
            conn.commit()
            conn.close()
            
            # Create a new memory instance for this chat and ensure it’s fresh
            memory = self._get_or_create_memory(chat_id)
            memory.clear()  # Explicitly clear memory to ensure no old data
            
            return {'chat_id': chat_id, 'chat_name': chat_name}

        @self.app.get('/chat/{user_id}/{chat_id}/messages')
        async def get_chat_messages(user_id: str, chat_id: int):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT message_type, message_text FROM messages WHERE chat_id = ? ORDER BY timestamp", (chat_id,))
            messages = cursor.fetchall()
            cursor.execute("SELECT chat_name FROM chats WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            chat = cursor.fetchone()
            conn.close()
            if not chat:
                raise HTTPException(status_code=404, detail="Chat not found")
            return {
                'chat_name': chat['chat_name'],
                'messages': [{'type': msg['message_type'], 'text': msg['message_text']} for msg in messages]
            }
        @self.app.post('/chat/{user_id}/{chat_id}')
        async def chat(user_id: str, chat_id: int, query: Query):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check the number of sent messages for this chat
            cursor.execute("SELECT COUNT(*) FROM messages WHERE chat_id = ? AND message_type = 'sent'", (chat_id,))
            sent_message_count = cursor.fetchone()[0]
            
            if sent_message_count >= 5:
                conn.close()
                app_logger.error("Message limit (5) reached for chat_id: %s", chat_id)
                raise HTTPException(status_code=403, detail="Message limit reached (5 messages per chat). Start a new chat to continue.")            
            # Increment messages_sent
            cursor.execute(
                "UPDATE users SET messages_sent = messages_sent + 1 WHERE user_id = ?",
                (user_id,)
            )
            
            # Proceed if limit not reached
            cursor.execute("SELECT summary FROM chats WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            chat = cursor.fetchone()
            if not chat:
                conn.close()
                raise HTTPException(status_code=404, detail="Chat not found")
            summary = chat['summary'] or ""  # Default to empty string if None

            # Store user message
            cursor.execute("INSERT INTO messages (chat_id, message_type, message_text, timestamp) VALUES (?, ?, ?, ?)",
                        (chat_id, "sent", query.question, datetime.now()))

            # Get or create memory for this chat
            memory = self._get_or_create_memory(chat_id)
            memory.buffer = summary
            history = memory.load_memory_variables({})['history']
            response = self.answer_generator.generator(query.question, history)

            # Store bot response
            cursor.execute("INSERT INTO messages (chat_id, message_type, message_text, timestamp) VALUES (?, ?, ?, ?)",
                        (chat_id, "received", response, datetime.now()))

            # Update summary
            memory.save_context({'input': query.question}, {'output': response})
            updated_summary = memory.buffer
            cursor.execute("UPDATE chats SET summary = ?, last_updated = ? WHERE chat_id = ?",
                        (updated_summary, datetime.now(), chat_id))
            conn.commit()
            conn.close()
            return {'response': response}    
        
        @self.app.delete('/chat/{user_id}/{chat_id}')
        async def delete_chat(user_id: str, chat_id: str):
            conn = get_db_connection()
            cursor = conn.cursor()
            # Clear the summary before deletion
            cursor.execute("UPDATE chats SET summary = '' WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            cursor.execute("DELETE FROM chats WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            if cursor.rowcount == 0:
                conn.close()
                raise HTTPException(status_code=404, detail='Chat not found')
            cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            conn.commit()
            conn.close()
            # Clear memory for this chat
            if chat_id in self.chat_memories:
                self.chat_memories[chat_id].clear()  # Clear the memory buffer
                del self.chat_memories[chat_id]  # Remove it from the dictionary
            return {'status': 'success'}

chatbot_api = ChatbotAPI()
app = chatbot_api.app
