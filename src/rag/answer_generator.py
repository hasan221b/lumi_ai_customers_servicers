from langchain.prompts import PromptTemplate
<<<<<<< HEAD
from langchain_core.runnables import RunnablePassthrough,RunnableLambda
from langchain.memory import ConversationBufferWindowMemory,ConversationSummaryMemory
=======
<<<<<<< HEAD
from langchain_core.runnables import RunnablePassthrough,RunnableLambda
from langchain.memory import ConversationBufferWindowMemory,ConversationSummaryMemory
=======
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
>>>>>>> 8bbcfc6 (Added some features to UI and modified app.py)
>>>>>>> c30e052 (Fixed bugs and added new features)
from src.utils.logger import pipeline_logger
import re

class AnswerGenerator:
<<<<<<< HEAD
    def __init__(self,llm,retriever,sentiment_analyzer,zero_shot_model):

=======
<<<<<<< HEAD
    def __init__(self,llm,retriever,sentiment_analyzer,zero_shot_model):

=======
    def __init__(self, llm, retriever, sentiment_analyzer, zero_shot_model):
>>>>>>> 8bbcfc6 (Added some features to UI and modified app.py)
>>>>>>> c30e052 (Fixed bugs and added new features)
        '''
        Setting up answer generator with chat memory and sentiment analysis.
        
        Args:
            llm: LLM model (e.g., gpt-4o-mini)
            retriever: A retriever method
            sentiment_analyzer: Sentiment analysis pipeline
<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
            zero_shot_model: Zero-shot classification model
>>>>>>> 8bbcfc6 (Added some features to UI and modified app.py)
>>>>>>> c30e052 (Fixed bugs and added new features)
        '''
        self.llm_model = llm
        self.retriever = retriever
        self.sentiment_analyzer = sentiment_analyzer
        self.zero_shot_model = zero_shot_model
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> c30e052 (Fixed bugs and added new features)
        #self.memory = ConversationBufferWindowMemory(
        #    memory_key="history",
        #    input_key="question",
        #    k=10  
        #)
        self.memory = ConversationSummaryMemory(
            memory_key="history",      
            input_key="question",      
            llm=llm
        )
        self.intents = ["shipping", "returns", "payment", "product_info", "other"]

        self.prompt = PromptTemplate(
            input_variables=['history', 'context', 'question', 'sentiment',
                             'sentimentS','suggestions','topic','needs_clarification'],

            template='''  You are an expert E-commerce customer support assistant named Sage. 
            Use the following conversation history and context to answer the question:
                        
            Context:\n{context}\n\n
            
            Question:\n{question}\n\n
            
            The question is talking about: {topic}\n\n
            Answer:\n
            {needs_clarification}\n
            Additionally, here are some related topics you might find helpful:\n{suggestions}
                '''
                )
<<<<<<< HEAD
=======
=======
        self.intents = ["shipping", "returns", "payment", "product_info", "other"]
        self.greeting_keywords = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        self.prompt = PromptTemplate(
            input_variables=['history', 'context', 'question', 'sentiment',
                             'sentimentS', 'suggestions', 'topic', 'needs_clarification'],
            template='''You are an expert E-commerce customer support assistant named Lumi. 
                    Use the following conversation history and context to answer the question naturally and helpfully:
                                
                    Conversation History:\n{history}\n\n
                    Context:\n{context}\n\n
                    Question:\n{question}\n\n
                    {needs_clarification}
                    {suggestions}
                    '''
        )
>>>>>>> 8bbcfc6 (Added some features to UI and modified app.py)
>>>>>>> c30e052 (Fixed bugs and added new features)
        self.rag_chain = (
            {
                'history': RunnableLambda(lambda x: x['history']),
                'context': lambda x: self._retrieve_main_context(x['question']),
                'question': lambda x: x['question'],
                'sentiment': lambda x: self._get_sentiment_label(x['question']),
                'sentimentS': lambda x: self._get_sentiment_score(x['question']),
                'suggestions': lambda x: self._retrieve_suggested_context(x['question']),
                'topic': lambda x: self.classify_intent(x['question']),
                'needs_clarification': lambda x: self.f_intent_confidence(x['question'])
            }
            | self.prompt
            | self.llm_model
        )

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> c30e052 (Fixed bugs and added new features)

    def _retrieve_main_context(self,question):
        """Retrieve main context using the retriever."""
        main_context,_= self.retriever.retriever(question)
        return main_context
    
    def _retrieve_suggested_context(self,question):
        """Retrieve main context using the retriever."""
        _,suggested_context= self.retriever.retriever(question)
        return suggested_context
    
    def _get_sentiment_label(self,question):
        """Get sentiment label from the sentiment analyzer."""
<<<<<<< HEAD
=======
=======
    def is_greeting(self, question):
        """Check if the input is a greeting."""
        question_lower = question.lower().strip()
        return any(keyword in question_lower for keyword in self.greeting_keywords) and len(question_lower.split()) <= 3
    def _retrieve_main_context(self, question):
        main_context, _ = self.retriever.retriever(question)
        return main_context
    
    def _retrieve_suggested_context(self, question):
        _, suggested_context = self.retriever.retriever(question)
        return suggested_context
    
    def _get_sentiment_label(self, question):
>>>>>>> 8bbcfc6 (Added some features to UI and modified app.py)
>>>>>>> c30e052 (Fixed bugs and added new features)
        try:
            sentiment_result = self.sentiment_analyzer(question)[0]
            return sentiment_result['label']
        except Exception as e:
            pipeline_logger.warning(f"Sentiment analysis failed: {e}. Defaulting to NEUTRAL.")
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> c30e052 (Fixed bugs and added new features)
            return "NEUTRA"

    def _get_sentiment_score(self,question):
        """Get sentiment score from the sentiment analyzer."""
<<<<<<< HEAD
=======
=======
            return "NEUTRAL"

    def _get_sentiment_score(self, question):
>>>>>>> 8bbcfc6 (Added some features to UI and modified app.py)
>>>>>>> c30e052 (Fixed bugs and added new features)
        try:
            sentiment_result = self.sentiment_analyzer(question)[0]
            return sentiment_result['score']
        except Exception as e:
            pipeline_logger.warning(f"Sentiment score retrieval failed: {e}. Defaulting to 0.5.")
            return 0.5
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> c30e052 (Fixed bugs and added new features)
        


    def classify_intent(self,question):
        result = self.zero_shot_model(question, self.intents)
        return result['labels'][0]

    def f_intent_confidence(self,question):
        
        result = self.zero_shot_model(question, self.intents)
        confidence =  result['scores'][0]
        print('confidence',confidence)
        if confidence < 0.6:
            return "I'm not entirely sure I understood your question. Please clarify!"
        else:
            return ""
        

    def generator(self,question:str,history: str) -> str:
        '''
        Generate a response using the RAG pipeline with memory and sentiment analysis.
        
        Args:
            question: The user's question as a string
        
        Returns:
            cleaned_response: A generated response based on context, history, and sentiment'''
        
        try:
            pipeline_logger.info(f'Generating response for question: {question}')
            response = self.rag_chain.invoke({'question': question, 'history': history})

            pipeline_logger.info('Response generation compleated successfully')
            cleaned_response = re.sub(r'\*\*(.*?)\*\*',r'\1',response.content)

<<<<<<< HEAD
=======
=======

    def classify_intent(self, question):
        result = self.zero_shot_model(question, self.intents)
        top_intent = result['labels'][0]
        top_score = result['scores'][0]
        # If confidence is low or input is too generic, default to "other"
        if top_score < 0.7 or len(question.strip()) < 5:  # "Hello" is short and vague
            return "other"
        return top_intent

    def f_intent_confidence(self, question):
        result = self.zero_shot_model(question, self.intents)
        confidence = result['scores'][0]
        if confidence < 0.7 or len(question.strip()) < 5:
            return "I'm not sure what you're asking. How can I assist you today?"
        return ""

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
>>>>>>> 8bbcfc6 (Added some features to UI and modified app.py)
>>>>>>> c30e052 (Fixed bugs and added new features)
            return cleaned_response
        except Exception as e:
            pipeline_logger.error(f'Failed to generate response: {e}')
            raise RuntimeError(f'Generating response has failed: {str(e)}')