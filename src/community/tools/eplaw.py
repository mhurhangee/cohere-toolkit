from typing import Any, Dict, List

from community.tools import BaseTool

from dotenv import load_dotenv
import os
import weaviate
from weaviate.classes.config import Integrations
from weaviate.classes.query import Rerank

import cohere

co = cohere.Client()

load_dotenv()
cohere_api_key = os.getenv('COHERE_API_KEY')

class EPLaw(BaseTool):
  
    @classmethod
    def is_available(cls) -> bool:
        return True
    
    def call(self, parameters: dict, **kwargs: Any) -> List[Dict[str, Any]]:
        query = parameters.get("query", "")
        
        client = weaviate.connect_to_local(
			port=8088,
			grpc_port=50051,
			headers={
				"X_Cohere-Api-Key": cohere_api_key
			}
		)

        integrations = [
			Integrations.cohere(
				api_key=cohere_api_key,
				requests_per_minute_embeddings=40,
			),
		]
        client.integrations.configure(integrations)
        collection = client.collections.get("EPO_LEGAL_DOCS")
        preamble = """
Your role is to help user's answer questions about European patent law by generating search engine prompts for the User to search to find legal basis or the appropriate resources from the European Patent Office. You should return only a list of simpler questions. Do not include the original question or answers in your response. Always use the following format:

>>> Search engine prompt
>>> Search engine prompt
"""
        response = co.chat(
			model="command-r-plus",
			preamble=preamble,
			message=query,
		)

        generated_questions = response.text.split(">>>")[1:]
        generated_questions = [ q.strip() for q in generated_questions if q.strip() != ""]  
        generated_questions.append(query)
        
        search_results = []
        for question in generated_questions:
            search_prompts = co.chat(
                search_queries_only=True,
                model="command-r-plus",
                message=question,
            )
            for search_query in search_prompts.search_queries:
                search_results.append(search_query.text)
        
        object_full = []

        for prompt in search_results:
            response = collection.query.hybrid(
                query=prompt, 
                limit=5,
                rerank=Rerank(
                    prop="text",
                    query=query,
                )
            )
            for obj in response.objects:
                object_full.append(obj) 
            
        unique_objects = {obj.uuid: obj for obj in object_full}

        sorted_objects = sorted(unique_objects.values(), key=lambda x: x.metadata.rerank_score, reverse=True)
        
        sorted_objects = sorted_objects[:5]
        
        client.close()
        return [
            {
                "text": doc.properties.get("text", None),
                "title": doc.metadata.get("title", None),
                "url": doc.metadata.get("url", None),
            }
            for doc in sorted_objects
        ]