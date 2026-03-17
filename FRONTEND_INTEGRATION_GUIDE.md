# Frontend Integration Guide - Human-in-the-Loop Workflow

This guide explains how to integrate the interactive refinement workflow into the React frontend.

---

## Overview

The HITL system requires a new UI phase between trip planning and confirmation. Current flow:

```
User Input → Generate Itinerary → (Save/View)
```

New flow with HITL:

```
User Input → Generate Itinerary → Review & Refine → (Save/View)
```

---

## Component Architecture

### New Components to Create

```
src/components/
├── ReviewInterface.jsx          (Main review container)
│   ├── ReviewHeader.jsx         (Session info, progress)
│   ├── ActivityCard.jsx         (Individual activity display)
│   ├── AlternativesPanel.jsx    (Show alternatives)
│   ├── RefinementToolbar.jsx    (Replace/Remove/Swap buttons)
│   └── PreviewModal.jsx         (Final cost preview)
├── InteractiveRefinement.jsx    (Refinement controls)
├── FeedbackForm.jsx             (Post-trip survey)
└── UserAnalytics.jsx            (Trip history & insights)
```

### Modified Components

```
src/components/
├── ChatInterface.jsx            (Add "Review" button after planning)
├── ItineraryView.jsx            (Show review session link)
└── TripForm.jsx                 (Pass optimization data to review)
```

---

## Step-by-Step Implementation

### 1. Create ReviewInterface Component

**File: `src/components/ReviewInterface.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ActivityCard from './ActivityCard';
import AlternativesPanel from './AlternativesPanel';
import RefinementToolbar from './RefinementToolbar';
import PreviewModal from './PreviewModal';
import './ReviewInterface.css';

const ReviewInterface = ({ 
  userId, 
  itineraryId, 
  itinerary, 
  optimizationData,
  onApprove,
  onCancel 
}) => {
  const [sessionId, setSessionId] = useState(null);
  const [reviewPoints, setReviewPoints] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [currentActivityIndex, setCurrentActivityIndex] = useState(0);
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [selectedAlternative, setSelectedAlternative] = useState(null);
  const [refinements, setRefinements] = useState([]);
  const [showPreview, setShowPreview] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize review session
  useEffect(() => {
    const startReview = async () => {
      try {
        const response = await axios.post(
          'http://localhost:8000/api/review/start',
          {
            user_id: userId,
            itinerary_id: itineraryId,
            itinerary,
            optimization_data: optimizationData,
            places_data: itinerary.places || []
          }
        );

        setSessionId(response.data.session_id);
        setReviewPoints(response.data.review_points);
        setSuggestions(response.data.suggestions);
        setLoading(false);
      } catch (err) {
        setError('Failed to start review session');
        console.error(err);
        setLoading(false);
      }
    };

    startReview();
  }, [userId, itineraryId, itinerary, optimizationData]);

  // Get current activity
  const currentActivity = reviewPoints[currentActivityIndex];

  // Handle activity navigation
  const goToNext = () => {
    if (currentActivityIndex < reviewPoints.length - 1) {
      setCurrentActivityIndex(currentActivityIndex + 1);
      setShowAlternatives(false);
    }
  };

  const goToPrevious = () => {
    if (currentActivityIndex > 0) {
      setCurrentActivityIndex(currentActivityIndex - 1);
      setShowAlternatives(false);
    }
  };

  // Handle refinement
  const handleRefinement = async (refinementType, details) => {
    try {
      const response = await axios.post(
        `http://localhost:8000/api/review/${sessionId}/refine`,
        {
          user_id: userId,
          itinerary_id: itineraryId,
          request_type: refinementType,
          day: currentActivity.day,
          time_slot: currentActivity.time_slot,
          details,
          reason: details.reason || ''
        }
      );

      // Track refinement
      setRefinements([...refinements, {
        type: refinementType,
        day: currentActivity.day,
        time_slot: currentActivity.time_slot
      }]);

      // Show confirmation
      alert(response.data.message);

      // Move to next activity
      goToNext();
    } catch (err) {
      setError('Failed to apply refinement');
      console.error(err);
    }
  };

  // Handle approve
  const handleApprove = async () => {
    try {
      const previewResponse = await axios.get(
        `http://localhost:8000/api/review/${sessionId}/preview`
      );

      const approveResponse = await axios.post(
        `http://localhost:8000/api/review/${sessionId}/approve`,
        {
          user_id: userId,
          itinerary_id: itineraryId,
          approved: true,
          final_itinerary: itinerary
        }
      );

      onApprove(approveResponse.data);
    } catch (err) {
      setError('Failed to approve itinerary');
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="review-container loading">
        <p>Initializing review session...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="review-container error">
        <p>{error}</p>
        <button onClick={onCancel}>Back</button>
      </div>
    );
  }

  return (
    <div className="review-interface">
      {/* Header */}
      <div className="review-header">
        <h2>Review Your Itinerary</h2>
        <div className="progress">
          Activity {currentActivityIndex + 1} of {reviewPoints.length}
        </div>
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="suggestions-panel">
          {suggestions.map((suggestion, idx) => (
            <div key={idx} className="suggestion">
              {suggestion}
            </div>
          ))}
        </div>
      )}

      {/* Main Activity Display */}
      <div className="review-main">
        <ActivityCard 
          activity={currentActivity}
          onShowAlternatives={() => setShowAlternatives(!showAlternatives)}
        />

        {/* Alternatives Panel */}
        {showAlternatives && (
          <AlternativesPanel 
            activity={currentActivity}
            alternatives={currentActivity.alternatives}
            onSelectAlternative={(alt) => {
              handleRefinement('replace', {
                place_name: alt.name,
                activity: alt.activity || alt.name,
                cost: alt.cost_estimate || currentActivity.cost,
                reason: `Selected ${alt.name} instead`
              });
            }}
          />
        )}

        {/* Refinement Toolbar */}
        <RefinementToolbar 
          activity={currentActivity}
          onReplace={() => setShowAlternatives(!showAlternatives)}
          onRemove={() => handleRefinement('remove', { reason: 'User removed activity' })}
          onSwap={() => alert('Swap feature coming soon')}
        />
      </div>

      {/* Navigation */}
      <div className="navigation-buttons">
        <button 
          onClick={goToPrevious}
          disabled={currentActivityIndex === 0}
          className="nav-btn prev"
        >
          ← Previous
        </button>

        <button 
          onClick={() => setShowPreview(true)}
          className="nav-btn preview"
        >
          Preview & Approve
        </button>

        <button 
          onClick={goToNext}
          disabled={currentActivityIndex === reviewPoints.length - 1}
          className="nav-btn next"
        >
          Next →
        </button>
      </div>

      {/* Preview Modal */}
      {showPreview && (
        <PreviewModal 
          sessionId={sessionId}
          userId={userId}
          itineraryId={itineraryId}
          onApprove={handleApprove}
          onContinueReview={() => setShowPreview(false)}
          onCancel={onCancel}
        />
      )}
    </div>
  );
};

export default ReviewInterface;
```

---

### 2. Create ActivityCard Component

**File: `src/components/ActivityCard.jsx`**

```jsx
import React from 'react';
import './ActivityCard.css';

const ActivityCard = ({ activity, onShowAlternatives }) => {
  const getScoreColor = (score) => {
    if (score >= 0.85) return '#4CAF50';     // green
    if (score >= 0.70) return '#FFC107';     // yellow
    return '#FF9800';                        // orange
  };

  return (
    <div className="activity-card">
      {/* Header */}
      <div className="activity-header">
        <div className="day-time">
          <span className="day">Day {activity.day}</span>
          <span className="time">{activity.time_slot}</span>
        </div>
        <div className="score">
          <span 
            className="score-badge"
            style={{ backgroundColor: getScoreColor(activity.score) }}
          >
            {(activity.score * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Activity Info */}
      <div className="activity-info">
        <h3 className="place-name">{activity.place_name}</h3>
        <p className="activity-name">{activity.activity}</p>
      </div>

      {/* Details */}
      <div className="activity-details">
        <span className="duration">⏱️ {activity.duration}</span>
        <span className="cost">💰 ₹{activity.cost}</span>
      </div>

      {/* Reasoning */}
      <div className="reasoning">
        <h4>Why this activity?</h4>
        <p>{activity.reasoning}</p>
      </div>

      {/* Score Breakdown */}
      <div className="score-breakdown">
        <h4>Score Breakdown</h4>
        <div className="breakdown-bars">
          <div className="breakdown-item">
            <label>Relevance</label>
            <div className="bar">
              <div className="fill" style={{ width: '95%' }}></div>
            </div>
          </div>
          <div className="breakdown-item">
            <label>Popularity</label>
            <div className="bar">
              <div className="fill" style={{ width: '90%' }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* Alternatives Preview */}
      <button 
        onClick={onShowAlternatives}
        className="show-alternatives-btn"
      >
        👀 {activity.alternatives?.length || 0} Alternatives Available
      </button>
    </div>
  );
};

export default ActivityCard;
```

**File: `src/components/ActivityCard.css`**

```css
.activity-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin: 20px 0;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.day-time {
  display: flex;
  gap: 10px;
}

.day {
  background: #e3f2fd;
  color: #1976d2;
  padding: 5px 10px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 14px;
}

.time {
  background: #f3e5f5;
  color: #7b1fa2;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 14px;
}

.score-badge {
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 16px;
}

.place-name {
  font-size: 20px;
  margin: 10px 0 5px 0;
  color: #333;
}

.activity-name {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.activity-details {
  display: flex;
  gap: 20px;
  margin: 15px 0;
  font-size: 14px;
}

.reasoning {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
  margin: 15px 0;
}

.reasoning h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #555;
}

.reasoning p {
  margin: 0;
  color: #666;
  line-height: 1.5;
}

.show-alternatives-btn {
  width: 100%;
  padding: 10px;
  background: #e8eaf6;
  border: 1px solid #c5cae9;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #3f51b5;
  font-weight: bold;
  margin-top: 15px;
}

.show-alternatives-btn:hover {
  background: #d1c4e9;
}
```

---

### 3. Create AlternativesPanel Component

**File: `src/components/AlternativesPanel.jsx`**

```jsx
import React from 'react';
import './AlternativesPanel.css';

const AlternativesPanel = ({ activity, alternatives, onSelectAlternative }) => {
  return (
    <div className="alternatives-panel">
      <h3>Alternative Options ({alternatives?.length || 0})</h3>
      
      <div className="alternatives-list">
        {alternatives?.map((alt, idx) => (
          <div key={idx} className="alternative-item">
            <div className="alt-header">
              <h4>{alt.name}</h4>
              <span className="rating">⭐ {alt.rating}</span>
            </div>

            <div className="alt-info">
              <p className="why-similar">
                {alt.why_similar || alt.reasoning}
              </p>
              
              {alt.cost_estimate && (
                <div className="cost-compare">
                  Current: ₹{activity.cost} → Alternative: ₹{alt.cost_estimate}
                </div>
              )}

              {alt.score && (
                <div className="score-compare">
                  Score: {(alt.score * 100).toFixed(0)}%
                  {alt.score > activity.score ? 
                    <span className="better">↑ Better</span> : 
                    <span className="similar">→ Similar</span>
                  }
                </div>
              )}
            </div>

            <button 
              onClick={() => onSelectAlternative(alt)}
              className="select-alternative-btn"
            >
              Choose This
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlternativesPanel;
```

**File: `src/components/AlternativesPanel.css`**

```css
.alternatives-panel {
  background: #fff9c4;
  border: 2px solid #fbc02d;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
}

.alternatives-panel h3 {
  margin: 0 0 15px 0;
  color: #f57f17;
  font-size: 16px;
}

.alternatives-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alternative-item {
  background: white;
  border: 1px solid #fdd835;
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.alternative-item:hover {
  background: #fffde7;
  transform: translateX(4px);
}

.alt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.alt-header h4 {
  margin: 0;
  font-size: 14px;
  color: #333;
}

.rating {
  font-size: 12px;
  color: #f57c00;
}

.why-similar {
  font-size: 12px;
  color: #666;
  margin: 6px 0;
  line-height: 1.4;
}

.cost-compare {
  font-size: 12px;
  color: #d32f2f;
  margin: 6px 0;
}

.score-compare {
  font-size: 12px;
  color: #388e3c;
  margin: 6px 0;
}

.better {
  color: #388e3c;
  font-weight: bold;
  margin-left: 5px;
}

.similar {
  color: #666;
  margin-left: 5px;
}

.select-alternative-btn {
  width: 100%;
  padding: 8px;
  background: #fbc02d;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  color: #333;
  margin-top: 8px;
}

.select-alternative-btn:hover {
  background: #f9a825;
}
```

---

### 4. Create RefinementToolbar Component

**File: `src/components/RefinementToolbar.jsx`**

```jsx
import React from 'react';
import './RefinementToolbar.css';

const RefinementToolbar = ({ 
  activity, 
  onReplace, 
  onRemove, 
  onSwap 
}) => {
  return (
    <div className="refinement-toolbar">
      <h4>Quick Actions</h4>
      
      <div className="buttons">
        <button 
          onClick={onReplace}
          className="action-btn replace-btn"
          title="Choose from alternatives"
        >
          🔄 Replace with Alternative
        </button>

        <button 
          onClick={onRemove}
          className="action-btn remove-btn"
          title="Remove this activity from itinerary"
        >
          ❌ Remove Activity
        </button>

        <button 
          onClick={onSwap}
          className="action-btn swap-btn"
          title="Move to different time"
        >
          ⏱️ Change Time Slot
        </button>
      </div>
    </div>
  );
};

export default RefinementToolbar;
```

**File: `src/components/RefinementToolbar.css`**

```css
.refinement-toolbar {
  background: #e8f5e9;
  border: 1px solid #81c784;
  border-radius: 8px;
  padding: 15px;
  margin: 20px 0;
}

.refinement-toolbar h4 {
  margin: 0 0 12px 0;
  color: #2e7d32;
  font-size: 14px;
}

.buttons {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
}

.action-btn {
  padding: 10px;
  border: 1px solid #4caf50;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  transition: all 0.3s ease;
}

.replace-btn:hover {
  background: #c8e6c9;
  border-color: #2e7d32;
}

.remove-btn:hover {
  background: #ffebee;
  border-color: #c62828;
}

.swap-btn:hover {
  background: #e3f2fd;
  border-color: #1565c0;
}

@media (max-width: 600px) {
  .buttons {
    grid-template-columns: 1fr;
  }
}
```

---

### 5. Create PreviewModal Component

**File: `src/components/PreviewModal.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './PreviewModal.css';

const PreviewModal = ({ 
  sessionId, 
  userId,
  itineraryId,
  onApprove, 
  onContinueReview,
  onCancel 
}) => {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        const response = await axios.get(
          `http://localhost:8000/api/review/${sessionId}/preview`
        );
        setPreview(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Failed to load preview', err);
        setLoading(false);
      }
    };

    fetchPreview();
  }, [sessionId]);

  if (loading) {
    return <div className="modal-overlay"><div className="modal">Loading...</div></div>;
  }

  if (!preview) {
    return <div className="modal-overlay"><div className="modal">Failed to load preview</div></div>;
  }

  return (
    <div className="modal-overlay" onClick={onContinueReview}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Final Preview</h2>
          <button onClick={onContinueReview} className="close-btn">✕</button>
        </div>

        <div className="modal-content">
          {/* Cost Summary */}
          <div className="cost-summary">
            <div className="cost-box">
              <span className="label">Original Cost</span>
              <span className="amount">₹{preview.original_cost}</span>
            </div>
            <div className="arrow">→</div>
            <div className="cost-box highlight">
              <span className="label">Updated Cost</span>
              <span className="amount">₹{preview.updated_cost}</span>
            </div>
            <div className="change">
              <span className={preview.cost_change.includes('-') ? 'saved' : 'increase'}>
                {preview.cost_change}
              </span>
            </div>
          </div>

          {/* Budget Check */}
          <div className={`budget-check ${preview.within_budget ? 'good' : 'warning'}`}>
            {preview.within_budget ? '✅' : '⚠️'} 
            {preview.within_budget 
              ? 'Within budget' 
              : 'Exceeds budget'}
            <span className="percentage">({preview.budget_utilization}%)</span>
          </div>

          {/* Daily Highlights */}
          <div className="daily-highlights">
            <h3>Daily Highlights</h3>
            {preview.final_summary?.daily_highlights?.map((day, idx) => (
              <div key={idx} className="day-highlight">
                <h4>Day {day.day}: {day.theme}</h4>
                <p className="activities-count">{day.activities_count} activities</p>
                <ul>
                  {day.highlights?.slice(0, 3).map((h, i) => (
                    <li key={i}>{h}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Changes Made */}
          <div className="changes-made">
            <h3>Your Refinements</h3>
            <p className="refinement-count">
              {preview.changes_made?.refinements_count} changes made
            </p>
            {Object.entries(preview.changes_made?.refinement_types || {}).map(
              ([type, count]) => (
                <div key={type} className="change-badge">
                  {type.charAt(0).toUpperCase() + type.slice(1)}: {count}
                </div>
              )
            )}
          </div>
        </div>

        <div className="modal-actions">
          <button 
            onClick={onContinueReview}
            className="btn btn-secondary"
          >
            ← Back to Review
          </button>
          <button 
            onClick={onApprove}
            className="btn btn-primary"
          >
            ✨ Approve & Book
          </button>
          <button 
            onClick={onCancel}
            className="btn btn-danger"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default PreviewModal;
```

**File: `src/components/PreviewModal.css`**

```css
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 5px 40px rgba(0,0,0,0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.modal-content {
  padding: 20px;
}

.cost-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}

.cost-box {
  flex: 1;
  text-align: center;
}

.cost-box.highlight {
  background: #e8f5e9;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #81c784;
}

.label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.amount {
  display: block;
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.arrow {
  color: #999;
  font-size: 20px;
}

.change {
  text-align: center;
  font-weight: bold;
  font-size: 14px;
}

.saved {
  color: #388e3c;
}

.increase {
  color: #d32f2f;
}

.budget-check {
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 20px;
  font-size: 14px;
  font-weight: bold;
}

.budget-check.good {
  background: #e8f5e9;
  color: #2e7d32;
}

.budget-check.warning {
  background: #fff3e0;
  color: #e65100;
}

.percentage {
  font-size: 12px;
  margin-left: 5px;
  opacity: 0.8;
}

.daily-highlights h3 {
  font-size: 14px;
  margin: 15px 0 10px 0;
  color: #333;
}

.day-highlight {
  background: #f9f9f9;
  padding: 10px;
  margin: 8px 0;
  border-radius: 6px;
  border-left: 3px solid #1976d2;
}

.day-highlight h4 {
  margin: 0 0 5px 0;
  font-size: 13px;
}

.activities-count {
  font-size: 12px;
  color: #666;
  margin: 0 0 8px 0;
}

.day-highlight ul {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: #666;
}

.changes-made h3 {
  font-size: 14px;
  margin: 15px 0 10px 0;
}

.refinement-count {
  font-size: 12px;
  color: #666;
  margin: 0 0 8px 0;
}

.change-badge {
  display: inline-block;
  background: #e0e0e0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin-right: 8px;
  margin-bottom: 8px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #eee;
  justify-content: flex-end;
}

.btn {
  padding: 10px 15px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: bold;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #4CAF50;
  color: white;
}

.btn-primary:hover {
  background: #45a049;
}

.btn-secondary {
  background: #e0e0e0;
  color: #333;
}

.btn-secondary:hover {
  background: #d0d0d0;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-danger:hover {
  background: #da190b;
}
```

---

### 6. Create FeedbackForm Component

**File: `src/components/FeedbackForm.jsx`**

```jsx
import React, { useState } from 'react';
import axios from 'axios';
import './FeedbackForm.css';

const FeedbackForm = ({ userId, itineraryId, onSubmited, onCancel }) => {
  const [formData, setFormData] = useState({
    overall_satisfaction: 5,
    timing_fit: 5,
    cost_accuracy: 5,
    place_variety: 5,
    comments: '',
    what_went_well: [],
    what_could_improve: [],
    would_revisit: true,
    actual_expenses: {
      accommodation: 0,
      food: 0,
      activities: 0,
      transport: 0
    }
  });

  const [loading, setLoading] = useState(false);

  const handleRatingChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleTextChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleExpenseChange = (category, value) => {
    setFormData({
      ...formData,
      actual_expenses: {
        ...formData.actual_expenses,
        [category]: parseFloat(value) || 0
      }
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(
        'http://localhost:8000/api/feedback/submit',
        {
          user_id: userId,
          itinerary_id: itineraryId,
          ...formData
        }
      );

      onSubmited(response.data);
    } catch (error) {
      alert('Failed to submit feedback');
      console.error(error);
    }

    setLoading(false);
  };

  return (
    <div className="feedback-form-container">
      <h2>Trip Feedback</h2>
      <p className="subtitle">Help us improve by sharing your experience</p>

      <form onSubmit={handleSubmit}>
        {/* Satisfaction Ratings */}
        <div className="form-section">
          <h3>How satisfied were you?</h3>

          <div className="rating-group">
            <label>Overall Experience</label>
            <div className="stars">
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  key={star}
                  type="button"
                  className={`star ${formData.overall_satisfaction >= star ? 'active' : ''}`}
                  onClick={() => handleRatingChange('overall_satisfaction', star)}
                >
                  ⭐
                </button>
              ))}
            </div>
          </div>

          <div className="rating-group">
            <label>Timing and Pace</label>
            <div className="stars">
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  key={star}
                  type="button"
                  className={`star ${formData.timing_fit >= star ? 'active' : ''}`}
                  onClick={() => handleRatingChange('timing_fit', star)}
                >
                  ⭐
                </button>
              ))}
            </div>
          </div>

          <div className="rating-group">
            <label>Cost Accuracy</label>
            <div className="stars">
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  key={star}
                  type="button"
                  className={`star ${formData.cost_accuracy >= star ? 'active' : ''}`}
                  onClick={() => handleRatingChange('cost_accuracy', star)}
                >
                  ⭐
                </button>
              ))}
            </div>
          </div>

          <div className="rating-group">
            <label>Activity Variety</label>
            <div className="stars">
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  key={star}
                  type="button"
                  className={`star ${formData.place_variety >= star ? 'active' : ''}`}
                  onClick={() => handleRatingChange('place_variety', star)}
                >
                  ⭐
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* What Went Well */}
        <div className="form-section">
          <h3>What did you love about this trip?</h3>
          <textarea
            name="comments"
            value={formData.comments}
            onChange={handleTextChange}
            placeholder="Share your favorite moments and highlights..."
            rows="4"
          ></textarea>
        </div>

        {/* Suggestions for Improvement */}
        <div className="form-section">
          <h3>How can we improve?</h3>
          <textarea
            name="what_could_improve"
            value={formData.what_could_improve.join('\n')}
            onChange={(e) => setFormData({
              ...formData,
              what_could_improve: e.target.value.split('\n').filter(s => s.trim())
            })}
            placeholder="Any suggestions? (one per line)"
            rows="3"
          ></textarea>
        </div>

        {/* Actual Expenses */}
        <div className="form-section">
          <h3>Actual Expenses (Optional)</h3>
          <div className="expense-fields">
            {['accommodation', 'food', 'activities', 'transport'].map(category => (
              <div key={category} className="expense-field">
                <label>{category.charAt(0).toUpperCase() + category.slice(1)}</label>
                <input
                  type="number"
                  value={formData.actual_expenses[category]}
                  onChange={(e) => handleExpenseChange(category, e.target.value)}
                  placeholder="₹0"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Would Revisit */}
        <div className="form-section checkbox-section">
          <label>
            <input
              type="checkbox"
              checked={formData.would_revisit}
              onChange={(e) => setFormData({ ...formData, would_revisit: e.target.checked })}
            />
            Would you visit this destination again?
          </label>
        </div>

        {/* Buttons */}
        <div className="form-actions">
          <button type="button" onClick={onCancel} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? 'Submitting...' : 'Submit Feedback'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default FeedbackForm;
```

---

### 7. Integrate into ChatInterface

**Update: `src/components/ChatInterface.jsx`**

```jsx
// Add after itinerary is generated:

import ReviewInterface from './ReviewInterface';

// In component:
const [showReview, setShowReview] = useState(false);
const [generatedItinerary, setGeneratedItinerary] = useState(null);

// After planning:
if (showReview && generatedItinerary) {
  return (
    <ReviewInterface 
      userId={userId}
      itineraryId={generatedItinerary.itinerary_id}
      itinerary={generatedItinerary}
      optimizationData={generatedItinerary.optimization_data}
      onApprove={(approvalData) => {
        alert('Itinerary approved!');
        // Navigate to confirmation screen
      }}
      onCancel={() => setShowReview(false)}
    />
  );
}

// Add button to start review:
<button onClick={() => setShowReview(true)} className="review-btn">
  ✨ Review & Refine
</button>
```

---

## Testing the Integration

### 1. Start Backend
```bash
cd /Users/pandhari/Desktop/PlanMyTrip/backend
python -m uvicorn main:app --reload --port 8000
```

### 2. Start Frontend
```bash
cd /Users/pandhari/Desktop/PlanMyTrip/frontend
npm run dev
```

### 3. Test Flow
1. Generate itinerary
2. Click "Review & Refine"
3. Review activities
4. Make refinements
5. Preview & approve
6. Complete trip
7. Submit feedback

---

## CSS Organization

Create a `src/styles/` directory:

```
src/styles/
├── variables.css       (Colors, spacing, fonts)
├── reset.css           (Base styles)
└── responsive.css      (Mobile/tablet breakpoints)
```

**File: `src/styles/variables.css`**

```css
:root {
  /* Colors */
  --primary: #4CAF50;
  --secondary: #2196F3;
  --danger: #f44336;
  --warning: #FF9800;
  --success: #4CAF50;
  
  /* Spacing */
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  /* Fonts */
  --font-primary: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  --font-size-sm: 12px;
  --font-size-md: 14px;
  --font-size-lg: 16px;
  --font-size-xl: 20px;
}
```

---

## Summary

The frontend integration includes:

✅ **Review Interface** - Main container for HITL workflow
✅ **Activity Cards** - Display individual activities with reasoning
✅ **Alternatives Panel** - Show and select alternatives
✅ **Refinement Toolbar** - Quick action buttons
✅ **Preview Modal** - Final cost preview
✅ **Feedback Form** - Post-trip survey
✅ **User Analytics** - Trip history and insights

**Next Steps:**
1. Implement these components
2. Test with backend API
3. Add mobile responsiveness
4. Deploy frontend

