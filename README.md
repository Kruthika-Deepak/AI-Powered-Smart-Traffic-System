# 🚦 City Congestion Prediction & Mitigation Platform

A full-stack, machine-learning–driven system designed to **predict short-term urban traffic congestion and actively reduce it** using data-driven decision mechanisms such as adaptive signal control and proactive routing.

This project goes **beyond traffic visualization** by integrating **prediction, optimization, and simulation** into a deployable architecture.

---

## 📌 Problem Statement : Predicting and easing City congestion

Urban traffic congestion leads to:
- Increased travel time
- Fuel wastage and higher emissions
- Delayed emergency response
- Economic inefficiency

Most existing solutions are **reactive**.  
This platform is **predictive and prescriptive**.

---

## 🎯 System Capabilities

1. Predicts congestion **15–30 minutes ahead**
2. Identifies probable congestion causes
3. Applies mitigation strategies (signal optimization / rerouting)
4. Simulates impact before deployment
5. Visualizes live and future traffic conditions

---

## 🧠 Key Features

### 🔮 Congestion Prediction
- Time-series machine learning models
- Probability and confidence-based outputs
- Short-horizon forecasting

### 🚦 Traffic Signal Optimization
- Dynamic green-time allocation
- Peak-hour dominance handling
- Constraint-aware logic

### 🧪 Simulation Engine
- Baseline vs optimized scenario comparison
- Queue length and delay estimation
- KPI generation

### 🗺️ Interactive Dashboard
- Live congestion heatmaps
- Time-based future projection slider
- Performance metrics visualization

### 📊 Observability & Reliability
- Model accuracy monitoring
- Latency tracking
- Rule-based fallback mechanisms

---
## 📊 Dataset Description

The system uses **time-series traffic datasets** suitable for future prediction, including:
- Historical traffic flow and speed data
- Weather conditions
- Temporal features (hour, day, holiday, events)

These datasets enable:
- Lag-based features
- Rolling window statistics
- Short-term congestion forecasting

---

## ⚙️ Technology Stack

### Backend
- Python
- Redis (feature store / cache)
- supabase

### Machine Learning
- Scikit-learn / Random Forest
- Time-series feature engineering
- Hybrid rule + ML decision logic

### Frontend
- React / Next.js
- Mapbox / Leaflet
- WebSockets for real-time updates

### DevOps
- Docker
- REST APIs
- Cloud-ready deployment

---

## 📈 Evaluation Metrics

### Prediction Metrics
- MAE / RMSE
- Classification accuracy
- Confidence calibration

### System Impact Metrics
- Average waiting time reduction
- Queue length reduction
- Travel time improvement (%)

---

## 🧪 Simulation Results (Sample)

| Metric | Baseline | Optimized |
|------|---------|-----------|
| Avg Delay | 92 sec | 71 sec |
| Queue Length | 18 vehicles | 13 vehicles |
| Peak Congestion | High | Moderate |

*Metrics generated through simulation.*

---

## 🔐 Reliability & Fallbacks

- Input validation for all APIs
- Rate limiting
- Graceful degradation:
  - ML service failure triggers rule-based signal logic

npm run dev
