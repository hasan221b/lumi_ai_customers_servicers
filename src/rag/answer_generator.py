from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from src.utils.logger import pipeline_logger
import re

class AnswerGenerator:
    def __init__(self, llm, retriever, sentiment_analyzer):
        '''
        Setting up answer generator with chat memory and sentiment analysis.
        
        Args:
            llm: LLM model (e.g., gpt-4o-mini)
            retriever: A retriever method
            sentiment_analyzer: Sentiment analysis pipeline
        '''
        self.llm_model = llm
        self.retriever = retriever
        self.sentiment_analyzer = sentiment_analyzer
        self.intents = ["shipping", "returns", "payment", "product_info", "other"]
        self.greeting_keywords = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        self.thanking_keywords = ['Thank you','Thanks', 'Ok','bye', 'thx']
        self.prompt = PromptTemplate(
            input_variables=['history', 'context', 'question', 'sentiment',
                             'sentimentS', 'suggestions', 'topic', 'needs_clarification'],
            template='''
            you are an expert E-commerce customer support assistant named Lumi. 
            Use the following conversation history and context to answer the question naturally and helpfully:
                
            Conversation History:\n{history}\n\n
            Context:\n{context}\n\n
            Question:\n{question}\n\n

            if the question is not clearuse this suggetsions: {suggestions}
                        '''
        )
        self.rag_chain = (
            {
                'history': RunnableLambda(lambda x: x['history']),
                'context': lambda x: self._retrieve_main_context(x['question']),
                'question': lambda x: x['question'],
                'sentiment': lambda x: self._get_sentiment_label(x['question']),
                'sentimentS': lambda x: self._get_sentiment_score(x['question']),
                'suggestions': lambda x: self._retrieve_suggested_context(x['question']),
            }
            | self.prompt
            | self.llm_model
        )

    def _retrieve_main_context(self, question):
        main_context, _ = self.retriever.retriever(question)
        return main_context
    
    def _retrieve_suggested_context(self, question):
        _, suggested_context = self.retriever.retriever(question)
        return suggested_context
    
    def _get_sentiment_label(self, question):
        try:
            sentiment_result = self.sentiment_analyzer(question)[0]
            return sentiment_result['label']
        except Exception as e:
            pipeline_logger.warning(f"Sentiment analysis failed: {e}. Defaulting to NEUTRAL.")
            return "NEUTRAL"

    def _get_sentiment_score(self, question):
        try:
            sentiment_result = self.sentiment_analyzer(question)[0]
            return sentiment_result['score']
        except Exception as e:
            pipeline_logger.warning(f"Sentiment score retrieval failed: {e}. Defaulting to 0.5.")
            return 0.5
    def is_greeting(self, question):
        """Check if the input is a greeting."""
        question_lower = question.lower().strip()
        return any(keyword in question_lower for keyword in self.greeting_keywords) and len(question_lower.split()) <= 3
    
    def generator(self, question: str, history: str) -> str:
        '''
        Generate a response using the RAG pipeline with provided history and sentiment analysis.
        
        Args:
            question: The user's question as a string
            history: The conversation history as a string
        
        Returns:
            cleaned_response: A generated response based on context, history, and sentiment
        '''
        try:
            pipeline_logger.info(f'Generating response for question: {question}')
            
            # Handle greetings specially
            if self.is_greeting(question):
                pipeline_logger.info('Detected greeting, returning simple response')
                return "Hello! How can I assist you today?"
            # Proceed with RAG pipeline for non-greetings
            response = self.rag_chain.invoke({'question': question, 'history': history})
            pipeline_logger.info('Response generation completed successfully')
            cleaned_response = re.sub(r'\*\*(.*?)\*\*', r'\1', response.content)
            return cleaned_response
        except Exception as e:
            pipeline_logger.error(f'Failed to generate response: {e}')
            raise RuntimeError(f'Generating response has failed: {str(e)}')
