from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
from datetime import datetime

class AIJobMatcher:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.learning_data_path = 'data/learning_data.json'
        self.load_learning_data()
        
    def load_learning_data(self):
        """Load historical application data for learning"""
        if os.path.exists(self.learning_data_path):
            with open(self.learning_data_path, 'r') as f:
                self.learning_data = json.load(f)
        else:
            self.learning_data = {
                "successful_applications": [],
                "unsuccessful_applications": [],
                "skill_weights": {},
                "company_preferences": {}
            }
    
    def save_learning_data(self):
        """Save learning data to file"""
        os.makedirs(os.path.dirname(self.learning_data_path), exist_ok=True)
        with open(self.learning_data_path, 'w') as f:
            json.dump(self.learning_data, f)
    
    def calculate_job_similarity(self, job1: Dict[str, Any], job2: Dict[str, Any]) -> float:
        """Calculate similarity between two jobs using embeddings"""
        desc1 = f"{job1['title']} {job1['description']}"
        desc2 = f"{job2['title']} {job2['description']}"
        
        embedding1 = self.embedding_model.encode(desc1)
        embedding2 = self.embedding_model.encode(desc2)
        
        return cosine_similarity([embedding1], [embedding2])[0][0]
    
    def update_skill_weights(self, job: Dict[str, Any], success: bool):
        """Update skill weights based on application success"""
        for skill in job.get('required_skills', []):
            if skill not in self.learning_data['skill_weights']:
                self.learning_data['skill_weights'][skill] = 0.5
            
            if success:
                self.learning_data['skill_weights'][skill] += 0.1
            else:
                self.learning_data['skill_weights'][skill] -= 0.1
            
            # Keep weights between 0 and 1
            self.learning_data['skill_weights'][skill] = max(0, min(1, 
                self.learning_data['skill_weights'][skill]))
    
    def update_company_preferences(self, company: str, success: bool):
        """Update company preferences based on application success"""
        if company not in self.learning_data['company_preferences']:
            self.learning_data['company_preferences'][company] = 0.5
        
        if success:
            self.learning_data['company_preferences'][company] += 0.1
        else:
            self.learning_data['company_preferences'][company] -= 0.1
        
        # Keep preferences between 0 and 1
        self.learning_data['company_preferences'][company] = max(0, min(1,
            self.learning_data['company_preferences'][company]))
    
    def record_application_outcome(self, job: Dict[str, Any], success: bool):
        """Record the outcome of an application for learning"""
        application_data = {
            "job": job,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            self.learning_data['successful_applications'].append(application_data)
        else:
            self.learning_data['unsuccessful_applications'].append(application_data)
        
        self.update_skill_weights(job, success)
        self.update_company_preferences(job['company'], success)
        self.save_learning_data()
    
    def calculate_job_score(self, job: Dict[str, Any], resume_data: Dict[str, Any]) -> float:
        """Calculate a score for how well the job matches the resume"""
        # Base similarity score
        job_desc = f"{job['title']} {job['description']}"
        resume_text = resume_data['raw_text']
        
        job_embedding = self.embedding_model.encode(job_desc)
        resume_embedding = self.embedding_model.encode(resume_text)
        
        similarity_score = cosine_similarity([job_embedding], [resume_embedding])[0][0]
        
        # Skill match score
        skill_score = 0
        for skill in job.get('required_skills', []):
            if skill in [s['skill'] for s in resume_data['skills']]:
                skill_score += self.learning_data['skill_weights'].get(skill, 0.5)
        
        # Company preference score
        company_score = self.learning_data['company_preferences'].get(job['company'], 0.5)
        
        # Combine scores with weights
        final_score = (
            0.4 * similarity_score +
            0.4 * skill_score +
            0.2 * company_score
        )
        
        return final_score
    
    def rank_jobs(self, jobs: List[Dict[str, Any]], resume_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank jobs based on match score and learning data"""
        scored_jobs = []
        for job in jobs:
            score = self.calculate_job_score(job, resume_data)
            scored_jobs.append({
                **job,
                'match_score': score
            })
        
        # Sort by match score
        return sorted(scored_jobs, key=lambda x: x['match_score'], reverse=True)
    
    def filter_jobs(self, jobs: List[Dict[str, Any]], resume_data: Dict[str, Any], 
                   min_score: float = 0.6) -> List[Dict[str, Any]]:
        """Filter jobs based on match score threshold"""
        ranked_jobs = self.rank_jobs(jobs, resume_data)
        return [job for job in ranked_jobs if job['match_score'] >= min_score] 