#!/usr/bin/env python3
"""
Interactive QA matcher client with caching support.
"""

import argparse
import yaml
import numpy as np
import time
import os
import pickle
from sentence_transformers import SentenceTransformer

class QAMatcher:
    def __init__(self, yaml_file, model_name="all-MiniLM-L6-v2", no_cache=False):
        """Initialize the QA matcher with data and model."""
        self.model_name = model_name
        self.yaml_file = yaml_file
        self.no_cache = no_cache
        
        # Load data, model, and vectors (with caching)
        self.load_data_and_model()
        
        print("\nQA system ready! Type your questions or 'exit' to quit.\n")
    
    def load_qa_data(self, yaml_file):
        """Load QA pairs from YAML file."""
        with open(yaml_file, 'r') as file:
            return yaml.safe_load(file)
    
    def get_cache_path(self):
        """Get the path for the cache file based on YAML and model."""
        cache_dir = os.path.expanduser("~/.cache/qa_matcher")
        os.makedirs(cache_dir, exist_ok=True)
        
        yaml_hash = hash(open(self.yaml_file, 'rb').read())
        return os.path.join(
            cache_dir, 
            f"{os.path.basename(self.yaml_file)}_{self.model_name.replace('/', '_')}_{yaml_hash}.pkl"
        )
    
    def load_data_and_model(self):
        """Load data, model, and vectors with optional caching."""
        cache_path = self.get_cache_path()
        
        # Try to load from cache if allowed
        if not self.no_cache and os.path.exists(cache_path):
            start = time.time()
            print(f"Loading cached data from {cache_path}...", end="", flush=True)
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.qa_data = cache_data['qa_data']
            self.question_vectors = cache_data['question_vectors']
            print(f" Done! ({time.time() - start:.2f}s)")
            
            # Load model (still needed for new queries)
            start = time.time()
            print(f"Loading model {self.model_name}...", end="", flush=True)
            self.model = SentenceTransformer(self.model_name)
            print(f" Done! ({time.time() - start:.2f}s)")
        else:
            # Load everything from scratch
            start = time.time()
            print(f"Loading QA data from {self.yaml_file}...", end="", flush=True)
            self.qa_data = self.load_qa_data(self.yaml_file)
            print(f" Done! ({time.time() - start:.2f}s)")
            
            # Load model
            start = time.time()
            print(f"Loading model {self.model_name}...", end="", flush=True)
            self.model = SentenceTransformer(self.model_name)
            print(f" Done! ({time.time() - start:.2f}s)")
            
            # Encode questions
            start = time.time()
            print(f"Encoding {len(self.qa_data)} questions...", end="", flush=True)
            questions = [item["question"] for item in self.qa_data]
            self.question_vectors = self.model.encode(
                questions, 
                convert_to_numpy=True,
                batch_size=32,
                show_progress_bar=len(questions) > 100
            )
            # Normalize vectors
            self.question_vectors = self.question_vectors / np.linalg.norm(
                self.question_vectors, axis=1, keepdims=True
            )
            print(f" Done! ({time.time() - start:.2f}s)")
            
            # Save to cache if allowed
            if not self.no_cache:
                start = time.time()
                print(f"Saving cache to {cache_path}...", end="", flush=True)
                cache_data = {
                    'qa_data': self.qa_data,
                    'question_vectors': self.question_vectors,
                    'model_name': self.model_name
                }
                with open(cache_path, 'wb') as f:
                    pickle.dump(cache_data, f)
                print(f" Done! ({time.time() - start:.2f}s)")
    
    def find_best_match(self, query, top_k=1, threshold=0.6):
        """Find the best matching QA pair for a given query."""
        start = time.time()
        
        # Encode and normalize the query
        query_vector = self.model.encode(query)
        query_vector = query_vector / np.linalg.norm(query_vector)
        
        # Calculate dot product
        scores = np.dot(self.question_vectors, query_vector)
        
        # Get top k indices
        if len(scores) <= 1000:
            top_indices = np.argsort(scores)[-top_k:][::-1]
        else:
            top_indices = np.argpartition(scores, -top_k)[-top_k:]
            top_indices = top_indices[np.argsort(scores[top_indices])][::-1]
        
        # Prepare results
        results = []
        for idx in top_indices:
            score = scores[idx]
            if score >= threshold:
                results.append({
                    "question": self.qa_data[idx]["question"],
                    "answer": self.qa_data[idx]["answer"],
                    "score": float(score),
                })
        
        inference_time = time.time() - start
        return results, inference_time
    
    def run_interactive(self, top_k=1, threshold=0.6):
        """Run an interactive session."""
        while True:
            # Get query from user
            try:
                print("\n> ", end="", flush=True)
                query = input().strip()
                
                if query.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break
                
                if not query:
                    continue
                
                # Find matches
                matches, inference_time = self.find_best_match(query, top_k, threshold)
                
                # Print results
                if matches:
                    print(f"Found {len(matches)} match(es) in {inference_time:.4f}s:")
                    for i, match in enumerate(matches, 1):
                        print(f"\nMatch {i}:")
                        print(f"Question: {match['question']}")
                        print(f"Answer: {match['answer']}")
                        print(f"Confidence: {match['score']:.4f}")
                else:
                    print(f"No matches found above the confidence threshold ({inference_time:.4f}s)")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Interactive QA matching client")
    parser.add_argument("--yaml", "-y", required=True, help="Path to YAML file with QA pairs")
    #_"all-MiniLM-L6-v2", 
    parser.add_argument("--model", "-m", default='paraphrase-mpnet-base-v2',
                       help="Sentence transformer model to use")
    parser.add_argument("--top_k", "-k", type=int, default=1, 
                       help="Number of top matches to return")
    parser.add_argument("--threshold", "-t", type=float, default=0.7, 
                       help="Similarity threshold (0-1)")
    parser.add_argument("--no-cache", action="store_true",
                       help="Disable caching")
    
    args = parser.parse_args()
    
    # Create and run the QA matcher
    matcher = QAMatcher(args.yaml, args.model, args.no_cache)
    matcher.run_interactive(args.top_k, args.threshold)

if __name__ == "__main__":
    main()