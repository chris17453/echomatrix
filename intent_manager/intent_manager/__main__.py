#!/usr/bin/env python3
"""
QA Matcher with Embedding Search + Cross-Encoder Reranking
BSD-3 Licensed
"""

import argparse
import yaml
import numpy as np
import os
import pickle
import time
from sentence_transformers import SentenceTransformer, CrossEncoder

class qa_matcher:
    def __init__(self, yaml_file, model_name="paraphrase-mpnet-base-v2", cross_encoder_name="cross-encoder/ms-marco-MiniLM-L-6-v2", no_cache=False):
        self.yaml_file = yaml_file
        self.model_name = model_name
        self.cross_encoder_name = cross_encoder_name
        self.no_cache = no_cache
        self.load_data_and_models()
        print("\nQA system ready. Type your question or 'exit' to quit.\n")

    def load_qa_data(self, yaml_file):
        with open(yaml_file, 'r') as f:
            return yaml.safe_load(f)

    def get_cache_path(self):
        cache_dir = os.path.expanduser("~/.cache/qa_matcher")
        os.makedirs(cache_dir, exist_ok=True)
        yaml_hash = hash(open(self.yaml_file, 'rb').read())
        return os.path.join(cache_dir, f"{os.path.basename(self.yaml_file)}_{self.model_name.replace('/', '_')}_{yaml_hash}.pkl")

    def load_data_and_models(self):
        cache_path = self.get_cache_path()

        if not self.no_cache and os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            self.qa_data = cache_data['qa_data']
            self.question_vectors = cache_data['question_vectors']
            self.model = SentenceTransformer(self.model_name)
            self.cross_encoder = CrossEncoder(self.cross_encoder_name)
        else:
            self.qa_data = self.load_qa_data(self.yaml_file)
            self.model = SentenceTransformer(self.model_name)
            self.cross_encoder = CrossEncoder(self.cross_encoder_name)

            questions = [item['question'] for item in self.qa_data]
            vectors = self.model.encode(questions, convert_to_numpy=True, batch_size=32)
            self.question_vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

            if not self.no_cache:
                cache_data = {
                    'qa_data': self.qa_data,
                    'question_vectors': self.question_vectors,
                }
                with open(cache_path, 'wb') as f:
                    pickle.dump(cache_data, f)

    def find_best_match(self, query, top_k=5, threshold=0.5):
        query_vector = self.model.encode(query)
        query_vector = query_vector / np.linalg.norm(query_vector)

        scores = np.dot(self.question_vectors, query_vector)
        top_indices = np.argsort(scores)[-top_k:][::-1]

        candidates = []
        for idx in top_indices:
            candidates.append({
                'question': self.qa_data[idx]['question'],
                'answer': self.qa_data[idx]['answer'],
                'embed_score': float(scores[idx]),
            })

        rerank_pairs = [[query, c['question']] for c in candidates]
        cross_scores = self.cross_encoder.predict(rerank_pairs)

        for c, cs in zip(candidates, cross_scores):
            c['cross_score'] = float(cs)

        candidates = sorted(candidates, key=lambda x: x['cross_score'], reverse=True)

        final_matches = [c for c in candidates if c['cross_score'] >= threshold]

        return final_matches

    def run_interactive(self, top_k=5, threshold=0.5):
        while True:
            try:
                query = input("\n> ").strip()
                if query.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye.")
                    break
                if not query:
                    continue

                matches = self.find_best_match(query, top_k=top_k, threshold=threshold)

                if matches:
                    for idx, m in enumerate(matches, 1):
                        print(f"\nMatch {idx}:")
                        print(f"Question: {m['question']}")
                        print(f"Answer: {m['answer']}")
                        print(f"Score: {m['cross_score']:.4f}")
                else:
                    print("No good match found.")

            except KeyboardInterrupt:
                print("\nExiting.")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="QA Matcher with reranking")
    parser.add_argument("--yaml", "-y", default="qa.yaml", help="Path to QA YAML file")
    parser.add_argument("--model", "-m", default="paraphrase-mpnet-base-v2", help="SentenceTransformer model")
    parser.add_argument("--cross", "-c", default="cross-encoder/stsb-distilroberta-base", help="CrossEncoder model")

    parser.add_argument("--top_k", "-k", type=int, default=5, help="Top K candidates to rerank")
    parser.add_argument("--threshold", "-t", type=float, default=0.5, help="Confidence threshold")
    parser.add_argument("--no-cache", action="store_true", help="Disable cache")
    args = parser.parse_args()

    matcher = qa_matcher(args.yaml, args.model, args.cross, args.no_cache)
    matcher.run_interactive(args.top_k, args.threshold)

if __name__ == "__main__":
    main()
