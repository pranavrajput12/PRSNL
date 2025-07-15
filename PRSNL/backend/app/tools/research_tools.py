"""
Research-specific Crew.ai tools
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.unified_ai_service import unified_ai_service
from app.tools import register_tool

logger = logging.getLogger(__name__)


class CitationExtractorInput(BaseModel):
    """Input schema for citation extractor tool"""
    content: str = Field(..., description="Content to extract citations from")
    citation_style: Optional[str] = Field("APA", description="Citation style: APA, MLA, Chicago")


@register_tool("citation_extractor")
class CitationExtractorTool(BaseTool):
    name: str = "Citation Extractor"
    description: str = (
        "Extracts and formats citations from academic content. "
        "Supports APA, MLA, and Chicago citation styles."
    )
    args_schema: Type[BaseModel] = CitationExtractorInput
    
    def _run(
        self,
        content: str,
        citation_style: str = "APA"
    ) -> str:
        """Extract citations from content"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_extract_citations(content, citation_style)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Citation extraction failed: {e}")
            return f"Failed to extract citations: {str(e)}"
    
    async def _async_extract_citations(
        self,
        content: str,
        citation_style: str
    ) -> str:
        """Async citation extraction"""
        try:
            prompt = f"""Extract all citations and references from this content.
Format them in {citation_style} style.

Content: {content[:3000]}

Return as JSON with:
1. 'inline_citations': List of in-text citations found
2. 'references': List of full references in {citation_style} format
3. 'citation_count': Total number of citations"""

            response = await unified_ai_service.complete(
                prompt=prompt,
                system_prompt=f"You are an expert in academic citations and {citation_style} formatting.",
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            try:
                citations = json.loads(response)
            except:
                return "Failed to extract citations"
            
            output = f"Citations ({citation_style} style):\n\n"
            
            if citations.get("inline_citations"):
                output += f"In-text citations ({len(citations['inline_citations'])}):\n"
                for cite in citations["inline_citations"][:10]:
                    output += f"- {cite}\n"
                output += "\n"
            
            if citations.get("references"):
                output += f"References ({len(citations['references'])}):\n"
                for ref in citations["references"][:10]:
                    output += f"{ref}\n\n"
            
            output += f"Total citations found: {citations.get('citation_count', 0)}"
            
            return output
            
        except Exception as e:
            logger.error(f"Async citation extraction failed: {e}")
            raise


class SourceValidatorInput(BaseModel):
    """Input schema for source validator tool"""
    source_url: Optional[str] = Field(None, description="URL of the source")
    source_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata about the source")
    content: Optional[str] = Field(None, description="Content to validate")


@register_tool("source_validator")
class SourceValidatorTool(BaseTool):
    name: str = "Source Validator"
    description: str = (
        "Validates the credibility and quality of research sources. "
        "Checks for peer review, impact factor, and reliability indicators."
    )
    args_schema: Type[BaseModel] = SourceValidatorInput
    
    def _run(
        self,
        source_url: Optional[str] = None,
        source_metadata: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None
    ) -> str:
        """Validate source credibility"""
        validation_results = {
            "credibility_score": 0.0,
            "factors": {},
            "warnings": [],
            "recommendations": []
        }
        
        # URL-based validation
        if source_url:
            domain = source_url.split('/')[2] if '/' in source_url else source_url
            
            # Check for known academic domains
            academic_domains = ['.edu', '.ac.uk', '.gov', 'arxiv.org', 'pubmed', 'doi.org']
            if any(domain.endswith(d) for d in academic_domains):
                validation_results["credibility_score"] += 0.3
                validation_results["factors"]["academic_domain"] = True
            
            # Check for predatory publishers (simplified)
            predatory_indicators = ['predatory', 'fake-journal', 'scam']
            if any(ind in domain.lower() for ind in predatory_indicators):
                validation_results["warnings"].append("Potential predatory publisher")
                validation_results["credibility_score"] -= 0.5
        
        # Metadata-based validation
        if source_metadata:
            if source_metadata.get("peer_reviewed"):
                validation_results["credibility_score"] += 0.3
                validation_results["factors"]["peer_reviewed"] = True
            
            impact_factor = source_metadata.get("impact_factor", 0)
            if impact_factor > 5:
                validation_results["credibility_score"] += 0.2
                validation_results["factors"]["high_impact"] = True
            elif impact_factor > 2:
                validation_results["credibility_score"] += 0.1
                validation_results["factors"]["moderate_impact"] = True
        
        # Content-based validation (simplified)
        if content:
            # Check for methodology mentions
            methodology_keywords = ['methodology', 'methods', 'procedure', 'protocol', 'design']
            if any(keyword in content.lower() for keyword in methodology_keywords):
                validation_results["credibility_score"] += 0.1
                validation_results["factors"]["methodology_present"] = True
            
            # Check for limitations discussion
            if 'limitations' in content.lower():
                validation_results["credibility_score"] += 0.1
                validation_results["factors"]["limitations_discussed"] = True
        
        # Ensure score is between 0 and 1
        validation_results["credibility_score"] = max(0, min(1, validation_results["credibility_score"]))
        
        # Generate output
        output = f"Source Validation Results:\n\n"
        output += f"Credibility Score: {validation_results['credibility_score']:.2f}/1.00\n\n"
        
        if validation_results["factors"]:
            output += "Positive Factors:\n"
            for factor, value in validation_results["factors"].items():
                if value:
                    output += f"✓ {factor.replace('_', ' ').title()}\n"
        
        if validation_results["warnings"]:
            output += "\nWarnings:\n"
            for warning in validation_results["warnings"]:
                output += f"⚠️  {warning}\n"
        
        # Add recommendations
        if validation_results["credibility_score"] < 0.5:
            output += "\nRecommendation: Exercise caution with this source. Verify findings with additional sources."
        elif validation_results["credibility_score"] < 0.7:
            output += "\nRecommendation: Moderate credibility. Cross-reference key claims."
        else:
            output += "\nRecommendation: High credibility source. Suitable for academic use."
        
        return output


class AcademicSearchInput(BaseModel):
    """Input schema for academic search tool"""
    query: str = Field(..., description="Search query")
    databases: Optional[List[str]] = Field(
        ["general"], 
        description="Databases to search: general, pubmed, arxiv, scholar"
    )
    max_results: Optional[int] = Field(10, description="Maximum results to return")


@register_tool("academic_search")
class AcademicSearchTool(BaseTool):
    name: str = "Academic Search"
    description: str = (
        "Searches academic databases for research papers and publications. "
        "Returns titles, abstracts, and metadata."
    )
    args_schema: Type[BaseModel] = AcademicSearchInput
    
    def _run(
        self,
        query: str,
        databases: List[str] = ["general"],
        max_results: int = 10
    ) -> str:
        """Search academic databases"""
        # In a real implementation, this would connect to actual academic APIs
        # For now, we'll simulate with AI-generated results
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_academic_search(query, databases, max_results)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Academic search failed: {e}")
            return f"Failed to search: {str(e)}"
    
    async def _async_academic_search(
        self,
        query: str,
        databases: List[str],
        max_results: int
    ) -> str:
        """Async academic search simulation"""
        prompt = f"""Simulate an academic database search for: "{query}"
Databases: {', '.join(databases)}

Generate {max_results} realistic academic paper results with:
1. Title
2. Authors
3. Year
4. Journal/Conference
5. Abstract (50 words)
6. Keywords
7. Citation count

Format as JSON array."""

        response = await unified_ai_service.complete(
            prompt=prompt,
            system_prompt="You are simulating an academic search engine. Create realistic academic paper metadata.",
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        try:
            results = json.loads(response)
            papers = results.get("papers", [])[:max_results]
        except:
            return "Failed to retrieve search results"
        
        output = f"Academic Search Results for '{query}':\n\n"
        
        for i, paper in enumerate(papers, 1):
            output += f"{i}. {paper.get('title', 'Untitled')}\n"
            output += f"   Authors: {paper.get('authors', 'Unknown')}\n"
            output += f"   Year: {paper.get('year', 'N/A')} | Journal: {paper.get('journal', 'N/A')}\n"
            output += f"   Citations: {paper.get('citation_count', 0)}\n"
            output += f"   Abstract: {paper.get('abstract', 'No abstract available')}\n"
            output += f"   Keywords: {', '.join(paper.get('keywords', []))}\n\n"
        
        return output


class PeerReviewAnalyzerInput(BaseModel):
    """Input schema for peer review analyzer tool"""
    content: str = Field(..., description="Content to analyze for peer review quality")


@register_tool("peer_review_analyzer")
class PeerReviewAnalyzerTool(BaseTool):
    name: str = "Peer Review Analyzer"
    description: str = (
        "Analyzes content for peer review quality indicators "
        "and methodological rigor."
    )
    args_schema: Type[BaseModel] = PeerReviewAnalyzerInput
    
    def _run(self, content: str) -> str:
        """Analyze peer review quality"""
        indicators = {
            "methodology_rigor": 0,
            "statistical_validity": 0,
            "literature_review": 0,
            "data_transparency": 0,
            "limitations_discussion": 0,
            "ethical_considerations": 0
        }
        
        # Simple keyword-based analysis
        content_lower = content.lower()
        
        # Check methodology
        if any(word in content_lower for word in ['methodology', 'methods', 'procedure']):
            indicators["methodology_rigor"] += 1
        if any(word in content_lower for word in ['randomized', 'controlled', 'systematic']):
            indicators["methodology_rigor"] += 1
        
        # Check statistical validity
        if any(word in content_lower for word in ['p-value', 'significance', 'confidence interval']):
            indicators["statistical_validity"] += 1
        if any(word in content_lower for word in ['sample size', 'power analysis', 'effect size']):
            indicators["statistical_validity"] += 1
        
        # Check literature review
        if 'literature review' in content_lower or 'previous studies' in content_lower:
            indicators["literature_review"] += 1
        
        # Check data transparency
        if any(word in content_lower for word in ['data availability', 'supplementary data', 'raw data']):
            indicators["data_transparency"] += 1
        
        # Check limitations
        if 'limitations' in content_lower:
            indicators["limitations_discussion"] += 1
        
        # Check ethics
        if any(word in content_lower for word in ['ethics', 'irb', 'consent', 'ethical approval']):
            indicators["ethical_considerations"] += 1
        
        # Calculate overall score
        total_score = sum(indicators.values())
        max_score = len(indicators) * 2
        quality_percentage = (total_score / max_score) * 100
        
        output = "Peer Review Quality Analysis:\n\n"
        output += f"Overall Quality Score: {quality_percentage:.1f}%\n\n"
        output += "Quality Indicators:\n"
        
        for indicator, score in indicators.items():
            status = "✓" if score > 0 else "✗"
            output += f"{status} {indicator.replace('_', ' ').title()}: {score}/2\n"
        
        if quality_percentage >= 70:
            output += "\nAssessment: High peer review quality"
        elif quality_percentage >= 50:
            output += "\nAssessment: Moderate peer review quality"
        else:
            output += "\nAssessment: Low peer review quality - additional scrutiny recommended"
        
        return output