import React, { useState, useEffect } from 'react';
import './InvestigationWorkflows.css';

interface CaseStudyStep {
  step: number;
  goal: string;
  example_question: string;
  pattern: string;
}

interface CaseStudy {
  id: string;
  title: string;
  description: string;
  category: string;
  steps: CaseStudyStep[];
}

interface Props {
  onSelectQuestion: (question: string) => void;
  isLoading: boolean;
}

const InvestigationWorkflows: React.FC<Props> = ({ onSelectQuestion, isLoading }) => {
  const [caseStudies, setCaseStudies] = useState<CaseStudy[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    loadCaseStudies();
  }, []);

  const loadCaseStudies = async () => {
    try {
      const response = await fetch('/api/case-studies');
      if (!response.ok) {
        throw new Error(`Failed to load case studies: ${response.statusText}`);
      }
      const data = await response.json();
      setCaseStudies(data.case_studies || []);
    } catch (err) {
      console.error('Failed to load case studies:', err);
      setLoadError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const selectedCaseStudy = caseStudies.find(cs => cs.id === selectedId);

  const handleQuestionClick = (question: string) => {
    onSelectQuestion(question);
  };

  if (caseStudies.length === 0 && !loadError) {
    return null; // Don't render if no case studies available
  }

  return (
    <div className="investigation-workflows">
      <button
        className="workflows-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        type="button"
      >
        📋 Investigation Workflows {isExpanded ? '▼' : '▶'}
      </button>

      {isExpanded && (
        <div className="workflows-content">
          {loadError ? (
            <div className="workflows-error">
              Failed to load investigation workflows: {loadError}
            </div>
          ) : (
            <>
              <select
                onChange={(e) => setSelectedId(e.target.value)}
                value={selectedId || ''}
                className="case-study-select"
              >
                <option value="">Select an investigation workflow...</option>
                {caseStudies.map(cs => (
                  <option key={cs.id} value={cs.id}>
                    {cs.title} ({cs.category})
                  </option>
                ))}
              </select>

              {selectedCaseStudy && (
                <div className="workflow-details">
                  <h3>{selectedCaseStudy.title}</h3>
                  <p className="workflow-description">{selectedCaseStudy.description}</p>
                  <div className="workflow-category">
                    <span className="category-badge">{selectedCaseStudy.category}</span>
                  </div>

                  <div className="workflow-steps">
                    {selectedCaseStudy.steps.map(step => (
                      <div key={step.step} className="workflow-step">
                        <div className="step-header">
                          <span className="step-number">Step {step.step}</span>
                          <span className="step-goal">{step.goal}</span>
                        </div>
                        <div className="step-pattern">Pattern: {step.pattern}</div>
                        <button
                          className="run-step-btn"
                          onClick={() => handleQuestionClick(step.example_question)}
                          disabled={isLoading}
                          type="button"
                        >
                          ▶ Run: "{step.example_question}"
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default InvestigationWorkflows;
