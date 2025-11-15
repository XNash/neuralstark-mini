#!/usr/bin/env python3
"""
COMPREHENSIVE RAG EVALUATION - PRECISION AND ACCURACY TESTING
Testing the RAG platform's accuracy and precision in retrieving small details from a large dataset.

This evaluation covers 30 test cases across 7 categories:
1. NEEDLE IN HAYSTACK (7 tests) - Finding specific details
2. SPELLING VARIATIONS (4 tests) - Robustness against typos
3. GRAMMATICAL VARIATIONS (4 tests) - Different phrasing
4. NUMERICAL PRECISION (6 tests) - Exact numbers, dates, quantities
5. COMPLEX MULTI-CRITERIA (3 tests) - Complex queries
6. MULTILINGUAL (3 tests) - French/English support
7. ABBREVIATIONS (2 tests) - Abbreviation handling
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple

# Get backend URL from environment
BACKEND_URL = "https://rag-analyzer.preview.emergentagent.com/api"

# Cerebras API key provided in review request
CEREBRAS_API_KEY = "csk-tdtfvf3xtvntkhm2k6enfky2cny9y9x686pxet3dp2h5dcvm"

class RAGComprehensiveEvaluator:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.session_id = "rag-eval-" + str(int(time.time()))
        self.category_scores = {}
        self.overall_score = 0
        
        # Load test cases
        with open('/app/rag_evaluation_tests.json', 'r') as f:
            self.test_data = json.load(f)
        
    def log_test(self, test_id, category, query, success, score, message, details=None):
        """Log test results with scoring"""
        result = {
            "test_id": test_id,
            "category": category,
            "query": query,
            "success": success,
            "score": score,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_id} ({category}): {message} [Score: {score}%]")
        if details and not success:
            print(f"   Details: {details}")
    
    def setup_api_key(self):
        """Configure Cerebras API key"""
        try:
            payload = {"cerebras_api_key": CEREBRAS_API_KEY}
            response = self.session.post(
                f"{self.base_url}/settings",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("✅ Cerebras API key configured successfully")
                return True
            else:
                print(f"❌ Failed to configure API key: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error configuring API key: {str(e)}")
            return False
    
    def verify_settings(self):
        """Verify API key is configured"""
        try:
            response = self.session.get(f"{self.base_url}/settings")
            if response.status_code == 200:
                data = response.json()
                if data.get("cerebras_api_key"):
                    print("✅ API key verification successful")
                    return True
                else:
                    print("❌ API key not found in settings")
                    return False
            else:
                print(f"❌ Settings verification failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error verifying settings: {str(e)}")
            return False
    
    def evaluate_response(self, response_text: str, sources: List[Dict], expected_answer: str, 
                         expected_correction: str = None, spelling_suggestion: str = None) -> Tuple[int, str]:
        """
        Evaluate response quality and return score (0-100) and explanation
        
        Scoring:
        - EXACT MATCH: 100% - Response contains exact expected value
        - SEMANTIC MATCH: 80% - Response is correct but phrased differently  
        - PARTIAL MATCH: 50% - Response contains some correct info but incomplete
        - NO MATCH: 0% - Response is incorrect or irrelevant
        - SPELLING DETECTED: +10 bonus if spelling_suggestion populated correctly
        """
        score = 0
        explanation = ""
        
        # Check for exact match
        if expected_answer.lower() in response_text.lower():
            score = 100
            explanation = f"EXACT MATCH: Found '{expected_answer}' in response"
        else:
            # Check for semantic match by looking for key components
            expected_parts = expected_answer.lower().split()
            found_parts = sum(1 for part in expected_parts if part in response_text.lower())
            
            if found_parts >= len(expected_parts) * 0.8:  # 80% of expected parts found
                score = 80
                explanation = f"SEMANTIC MATCH: Found {found_parts}/{len(expected_parts)} key components"
            elif found_parts >= len(expected_parts) * 0.4:  # 40% of expected parts found
                score = 50
                explanation = f"PARTIAL MATCH: Found {found_parts}/{len(expected_parts)} key components"
            else:
                score = 0
                explanation = f"NO MATCH: Found only {found_parts}/{len(expected_parts)} key components"
        
        # Bonus for spelling correction
        if expected_correction and spelling_suggestion:
            if expected_correction.lower() in spelling_suggestion.lower():
                score = min(100, score + 10)
                explanation += f" + SPELLING BONUS: Detected '{expected_correction}'"
        
        # Check source relevance
        if len(sources) == 0:
            score = max(0, score - 20)
            explanation += " - NO SOURCES PENALTY"
        
        return score, explanation
    
    def run_single_test(self, test_case: Dict, category: str) -> Dict:
        """Run a single test case"""
        test_id = test_case["test_id"]
        query = test_case["query"]
        expected_answer = test_case["expected_answer"]
        expected_correction = test_case.get("expected_correction")
        
        try:
            start_time = time.time()
            
            payload = {
                "message": query,
                "session_id": self.session_id + f"-{test_id.lower()}"
            }
            
            response = self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                sources = data.get("sources", [])
                spelling_suggestion = data.get("spelling_suggestion")
                
                # Evaluate response
                score, explanation = self.evaluate_response(
                    response_text, sources, expected_answer, expected_correction, spelling_suggestion
                )
                
                # Log detailed results
                details = {
                    "response_time_ms": response_time,
                    "response_length": len(response_text),
                    "sources_count": len(sources),
                    "spelling_suggestion": spelling_suggestion,
                    "expected_answer": expected_answer,
                    "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "source_files": [s.get("source", "unknown") for s in sources[:3]],
                    "relevance_scores": [s.get("relevance_score", 0) for s in sources[:3]],
                    "reranker_scores": [s.get("reranker_score", 0) for s in sources[:3]]
                }
                
                success = score >= 50  # Consider 50%+ as success
                self.log_test(test_id, category, query, success, score, explanation, details)
                
                return {
                    "test_id": test_id,
                    "success": success,
                    "score": score,
                    "explanation": explanation,
                    "details": details
                }
                
            elif response.status_code == 429:
                # Rate limit - still log as attempted
                self.log_test(test_id, category, query, False, 0, "API RATE LIMIT EXCEEDED", 
                            {"error": "429 - Rate limit exceeded"})
                return {"test_id": test_id, "success": False, "score": 0, "explanation": "Rate limit exceeded"}
                
            elif response.status_code == 401:
                # Auth error
                self.log_test(test_id, category, query, False, 0, "API AUTHENTICATION FAILED", 
                            {"error": f"401 - {response.text}"})
                return {"test_id": test_id, "success": False, "score": 0, "explanation": "Authentication failed"}
                
            else:
                # Other HTTP error
                self.log_test(test_id, category, query, False, 0, f"HTTP ERROR {response.status_code}", 
                            {"error": response.text})
                return {"test_id": test_id, "success": False, "score": 0, "explanation": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log_test(test_id, category, query, False, 0, f"REQUEST ERROR: {str(e)}")
            return {"test_id": test_id, "success": False, "score": 0, "explanation": f"Error: {str(e)}"}
    
    def run_category_tests(self, category_data: Dict) -> Dict:
        """Run all tests in a category"""
        category_name = category_data["category"]
        tests = category_data["tests"]
        
        print(f"\n🔍 TESTING CATEGORY: {category_name}")
        print(f"Description: {category_data['description']}")
        print(f"Tests: {len(tests)}")
        print("-" * 80)
        
        category_results = []
        total_score = 0
        successful_tests = 0
        
        for test_case in tests:
            result = self.run_single_test(test_case, category_name)
            category_results.append(result)
            total_score += result["score"]
            if result["success"]:
                successful_tests += 1
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Calculate category statistics
        avg_score = total_score / len(tests) if tests else 0
        success_rate = (successful_tests / len(tests)) * 100 if tests else 0
        
        category_summary = {
            "category": category_name,
            "total_tests": len(tests),
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "average_score": avg_score,
            "results": category_results
        }
        
        self.category_scores[category_name] = category_summary
        
        print(f"\n📊 CATEGORY SUMMARY: {category_name}")
        print(f"Success Rate: {success_rate:.1f}% ({successful_tests}/{len(tests)})")
        print(f"Average Score: {avg_score:.1f}%")
        
        return category_summary
    
    def run_comprehensive_evaluation(self):
        """Run the complete RAG evaluation"""
        print("🚀 STARTING COMPREHENSIVE RAG EVALUATION")
        print("=" * 80)
        print(f"Test Suite: {self.test_data['evaluation_metadata']['test_suite_name']}")
        print(f"Total Tests: {self.test_data['evaluation_metadata']['total_tests']}")
        print(f"Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Setup
        if not self.setup_api_key():
            print("❌ Failed to setup API key. Aborting evaluation.")
            return False
        
        if not self.verify_settings():
            print("❌ Failed to verify settings. Aborting evaluation.")
            return False
        
        # Run tests by category
        for category_data in self.test_data["test_categories"]:
            try:
                self.run_category_tests(category_data)
            except Exception as e:
                print(f"❌ Error in category {category_data['category']}: {str(e)}")
                continue
        
        # Generate final report
        self.generate_final_report()
        return True
    
    def generate_final_report(self):
        """Generate comprehensive evaluation report"""
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE RAG EVALUATION REPORT")
        print("=" * 80)
        
        # Overall statistics
        total_tests = sum(cat["total_tests"] for cat in self.category_scores.values())
        total_successful = sum(cat["successful_tests"] for cat in self.category_scores.values())
        overall_success_rate = (total_successful / total_tests) * 100 if total_tests > 0 else 0
        overall_avg_score = sum(cat["average_score"] for cat in self.category_scores.values()) / len(self.category_scores) if self.category_scores else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful Tests: {total_successful}")
        print(f"   Overall Success Rate: {overall_success_rate:.1f}%")
        print(f"   Overall Average Score: {overall_avg_score:.1f}%")
        
        # Category breakdown
        print(f"\n📈 CATEGORY BREAKDOWN:")
        for category, results in self.category_scores.items():
            print(f"   {category}:")
            print(f"      Success Rate: {results['success_rate']:.1f}% ({results['successful_tests']}/{results['total_tests']})")
            print(f"      Average Score: {results['average_score']:.1f}%")
        
        # Best and worst performing categories
        if self.category_scores:
            best_category = max(self.category_scores.items(), key=lambda x: x[1]['average_score'])
            worst_category = min(self.category_scores.items(), key=lambda x: x[1]['average_score'])
            
            print(f"\n🏆 BEST PERFORMING CATEGORY: {best_category[0]} ({best_category[1]['average_score']:.1f}%)")
            print(f"🔧 NEEDS IMPROVEMENT: {worst_category[0]} ({worst_category[1]['average_score']:.1f}%)")
        
        # Specific findings
        print(f"\n🔍 SPECIFIC FINDINGS:")
        
        # Needle in haystack performance
        if "NEEDLE_IN_HAYSTACK" in self.category_scores:
            nh_score = self.category_scores["NEEDLE_IN_HAYSTACK"]["average_score"]
            print(f"   Needle-in-Haystack Accuracy: {nh_score:.1f}% - {'✅ Excellent' if nh_score >= 80 else '⚠️ Needs Improvement' if nh_score >= 60 else '❌ Poor'}")
        
        # Spelling correction effectiveness
        if "SPELLING_VARIATIONS" in self.category_scores:
            sp_score = self.category_scores["SPELLING_VARIATIONS"]["average_score"]
            print(f"   Spelling Correction: {sp_score:.1f}% - {'✅ Working Well' if sp_score >= 70 else '⚠️ Partial' if sp_score >= 50 else '❌ Not Working'}")
        
        # Numerical precision
        if "NUMERICAL_PRECISION" in self.category_scores:
            num_score = self.category_scores["NUMERICAL_PRECISION"]["average_score"]
            print(f"   Numerical Precision: {num_score:.1f}% - {'✅ Accurate' if num_score >= 80 else '⚠️ Moderate' if num_score >= 60 else '❌ Inaccurate'}")
        
        # Complex query handling
        if "COMPLEX_MULTI_CRITERIA" in self.category_scores:
            mc_score = self.category_scores["COMPLEX_MULTI_CRITERIA"]["average_score"]
            print(f"   Complex Query Handling: {mc_score:.1f}% - {'✅ Advanced' if mc_score >= 70 else '⚠️ Basic' if mc_score >= 50 else '❌ Limited'}")
        
        # Multilingual support
        if "MULTILINGUAL" in self.category_scores:
            ml_score = self.category_scores["MULTILINGUAL"]["average_score"]
            print(f"   Multilingual Support: {ml_score:.1f}% - {'✅ Excellent' if ml_score >= 80 else '⚠️ Good' if ml_score >= 60 else '❌ Limited'}")
        
        # Examples of best and worst performance
        print(f"\n💡 EXAMPLES:")
        
        # Find best performing test
        best_test = max(self.test_results, key=lambda x: x["score"]) if self.test_results else None
        if best_test:
            print(f"   🏆 BEST PERFORMANCE: {best_test['test_id']} - {best_test['score']}%")
            print(f"      Query: '{best_test['query']}'")
            print(f"      Result: {best_test['message']}")
        
        # Find worst performing test
        worst_test = min(self.test_results, key=lambda x: x["score"]) if self.test_results else None
        if worst_test and worst_test != best_test:
            print(f"   🔧 NEEDS WORK: {worst_test['test_id']} - {worst_test['score']}%")
            print(f"      Query: '{worst_test['query']}'")
            print(f"      Result: {worst_test['message']}")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        if overall_avg_score >= 80:
            print("   ✅ RAG system shows excellent accuracy and precision")
            print("   ✅ Ready for production use with high-precision requirements")
        elif overall_avg_score >= 60:
            print("   ⚠️ RAG system shows good performance but has room for improvement")
            print("   ⚠️ Consider fine-tuning for better precision on specific details")
        else:
            print("   ❌ RAG system needs significant improvements")
            print("   ❌ Focus on enhancing retrieval accuracy and response precision")
        
        # Specific recommendations based on category performance
        for category, results in self.category_scores.items():
            if results['average_score'] < 60:
                if category == "NEEDLE_IN_HAYSTACK":
                    print("   🔧 Improve chunk size and overlap for better detail capture")
                elif category == "SPELLING_VARIATIONS":
                    print("   🔧 Enhance spell checking and fuzzy matching capabilities")
                elif category == "NUMERICAL_PRECISION":
                    print("   🔧 Add numerical entity recognition and exact matching")
                elif category == "COMPLEX_MULTI_CRITERIA":
                    print("   🔧 Improve query decomposition and multi-step reasoning")
                elif category == "MULTILINGUAL":
                    print("   🔧 Enhance multilingual embedding model and language detection")
        
        print("=" * 80)
        print("📋 EVALUATION COMPLETE")
        print("=" * 80)

def main():
    """Main execution function"""
    evaluator = RAGComprehensiveEvaluator()
    
    try:
        success = evaluator.run_comprehensive_evaluation()
        if success:
            print("\n✅ RAG evaluation completed successfully")
            return 0
        else:
            print("\n❌ RAG evaluation failed")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️ Evaluation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Evaluation failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())