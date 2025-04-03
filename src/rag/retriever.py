from src.utils.logger import pipeline_logger

class Retriever:
    '''
    Setting up a retriever
    Args:
        embedding_model: all-MiniLM-L6-v2 embedding model
        index: faiss index
        df: Faqs dataframe

    Returns:
        relevant_ans : relevant data from the datafram
    
    '''
    def __init__(self,embedding_model,index,df):
        self.embedding_model = embedding_model
        self.index = index
        self.df = df

    def retriever(self,query,top_k = 3, sug_k = 2):

        try:
            pipeline_logger.info('Retrieving relavent data')
            embedded_query = self.embedding_model.encode(query).reshape(1,-1)
            distances, indices = self.index.search(embedded_query,top_k+sug_k)
            
            main_indices = indices[0][:top_k]
            suggested_indices = indices[0][top_k:top_k+sug_k]

            main_answer = [self.df['answer'].iloc[idx] for idx in main_indices]
            main_context = '\n'.join(main_answer)
            if len(query.strip()) < 5 or max(distances[0][:top_k]) > 1.0:  # High distance means low relevance
                main_context = "No specific context available."
            pipeline_logger.info(f'Main context retrieved: {main_context}')
            suggested_questions = [self.df['question'].iloc[idx] for idx in suggested_indices]
            formated_suggestions = "\n".join([f"- Want to know about {sug}" for sug in suggested_questions])

            return main_context, formated_suggestions
        
        except Exception as e:
            pipeline_logger.error(f'Failed to retrieve relavent data: {e}')
            raise RuntimeError('Retrieving has failed')

            return main_context, formated_suggestions
        
        except Exception as e:
            pipeline_logger.error(f'Failed to retrieve relavent data: {e}')
            raise RuntimeError('Retrieving has failed')
