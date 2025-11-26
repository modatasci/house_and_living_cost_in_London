## London Housing Cost Visualization - Project Plan


### Phase 1: Early Functionality
**A. Travel cost calculator**
   - A simple UI where user can calculate the travel cost between their home and workplace
   - Deployment in Streamlit 
   - Data source: TfL transport api
   - Cost calculator -> route_calculator.py

**B. Inclusion of concil tax and average rent cost in**

  **B.1 Acquire datasets**:
   - London postcode boundaries (GeoJSON/Shapefile from OS Open Data or London Datastore)
   - Average rent per square meter by postcode/borough
   - Council tax data by borough
   - London postcode coordinates

 **B.2 Data cleaning & integration**:
   - Merge datasets on postcode/borough
   - Handle missing values
   - Calculate derived metrics
   - Export to clean CSV/JSON format

### Phase 2: Optimization of best accomodation location

**C. Build Interactive map visualization Streamlit UI**:
   - Postcode selection inputs (home & work)
   - Interactive map visualization
   - Cost breakdown display (rent, travel, council tax, total)
   - Filter/toggle options (property size, travel mode)

   **C.1 Build geospatial components**:
   - Create interactive London map using Folium or Plotly
   - Add postcode boundary overlays
   - Implement color-coding by cost metrics


### Phase 3: Refinement & Deployment
**D. Add enhancements**:
   - Comparison mode (multiple postcodes)
   - Affordability heatmap overlay
   - Data visualizations (charts for cost breakdown)

**E. Prepare for deployment**:
   - Create requirements.txt
   - Optimize data loading (caching)
   - Add documentation/README
   - Test locally

**F. Deploy to Streamlit Cloud**:
   - Push to GitHub repository
   - Connect to Streamlit Cloud
   - Configure deployment settings
   - Test production deployment

**Key Technologies**: Python, Streamlit, Folium/Plotly, Pandas, GeoPandas

---

## Phase 4: Future Development & Scaling

### Current Status (Completed)
✅ Streamlit app deployed with:
- TfL journey planning with multiple route options
- Council tax calculation by postcode
- Average rent prices by borough and bedroom category
- Cost comparison and export functionality
- Interactive journey maps

### Architecture Evolution Plan

**Recommended Architecture:**
```
User's Browser
    ↓
Custom Domain (Cloudflare) → Streamlit App (Frontend)
    ↓
FastAPI Backend (Railway/Render)
    ↓
Supabase (PostgreSQL Database)
```

**Why this approach:**
- Keep Streamlit as frontend (leverage existing Python knowledge)
- Separate backend logic for better scalability
- Database for persistent storage and caching
- No need to learn JavaScript/React initially

### Technology Stack Decisions

**1. Database Layer**
- **PostgreSQL**: Primary database (actual storage)
- **SQLAlchemy**: Python ORM to interact with database
- **Relationship**: SQLAlchemy = Python code to talk to PostgreSQL
- **Usage**: Store user data, cached API responses, historical trends

**2. Backend API**
- **FastAPI**: Python-based REST API framework
- **Purpose**:
  - Separate business logic from UI
  - Create reusable API endpoints
  - Better testing and maintainability
  - Foundation for future mobile apps

**3. Hosting Options**

| Component | Service | Cost | Notes |
|-----------|---------|------|-------|
| Database | Supabase | Free tier | PostgreSQL + Auth + Storage |
| Backend API | Railway or Render | $5-10/month | Easy Python deployment |
| Frontend | Streamlit Cloud | Free | Current deployment |
| Domain | Namecheap + Cloudflare | ~$12/year | Custom domain setup |

### Learning Roadmap (6 months)

**Month 1-2: SQL & Database Design**
- PostgreSQL basics
- SQLAlchemy ORM
- Database schema design
- CRUD operations
- **Resources**: PostgreSQL docs, SQLAlchemy tutorials

**Month 3: FastAPI**
- REST API principles
- FastAPI framework
- Pydantic for data validation
- API documentation with Swagger
- **Resources**: FastAPI official docs

**Month 4: Integration**
- Connect Streamlit → FastAPI → PostgreSQL
- Implement user authentication
- Migrate existing calculations to API endpoints
- Database migration from session state

**Month 5: Testing & DevOps**
- pytest for backend testing
- Docker basics
- CI/CD with GitHub Actions
- Environment management
- **Resources**: pytest docs, Docker tutorials

**Month 6: Advanced Features**
- Historical price tracking
- Email notifications
- PDF report generation
- Performance optimization

### Performance Optimization Strategy

**Current Bottlenecks:**
1. TfL API calls: ~500-2000ms
2. Streamlit reruns: Full page reload
3. No caching: Repeat searches hit API again

**Quick Wins (No architecture change needed):**
1. **Cache TfL API responses** using `@st.cache_data(ttl=3600)`
2. **Use `st.fragment()`** to reduce full page reruns
3. **Parallel data fetching** for journey + council tax + rent
4. **Expected improvement**: 30-50% faster

**Long-term (With backend migration):**
1. **Database caching**: Repeat searches from DB (0.5-1s vs 2-4s)
2. **Pre-loading**: Council tax & rent data always ready
3. **Background jobs**: Update price trends overnight
4. **Progressive loading**: Show results as they arrive
5. **Expected improvement**: 60-80% faster for cached queries

**Important Note:** Backend migration is primarily for features, not speed. Current app performance is acceptable. Migrate for:
- User accounts & saved preferences
- Historical data tracking
- API for other platforms
- Better code organization
- Learning experience

### Custom Domain Setup

**Option 1: Self-hosting (Recommended for learning)**
- Deploy Streamlit on Railway/Render
- Point custom domain directly to server
- Full control, ~$5-15/month

**Option 2: Reverse proxy (Cheapest)**
- Keep Streamlit Cloud deployment
- Use Cloudflare to mask `.streamlit.io` URL
- Point `yourdomain.com` → Streamlit app
- Cost: ~$12/year (domain only)

**Option 3: Streamlit Enterprise**
- Official custom domain support
- Requires team/enterprise plan
- ~$250-500/month
- Not recommended for personal projects

### Key Features to Add (Post-Backend)

**G. User Account System**
- Authentication (via Supabase Auth)
- Save favorite locations
- Persistent comparison history
- Email notifications for price changes

**H. Historical Data & Analytics**
- Track rent/council tax trends over time
- Price change alerts
- Predictive analytics for future costs
- Seasonal travel cost variations

**I. Enhanced Comparisons**
- Side-by-side area comparisons
- Affordability scoring algorithm
- Quality of life metrics integration
- School ratings, crime statistics

**J. Export & Sharing**
- PDF reports with maps
- Shareable comparison links
- Public comparison galleries
- Export to spreadsheet with formulas

**K. API & Integration**
- Public API for developers
- Zapier/IFTTT integration
- Mobile app (future consideration)

### When to Consider JavaScript/Frontend Frameworks

**Stick with Streamlit if:**
- App is data/analytics focused (current case)
- Team knows Python well
- Rapid prototyping is priority
- Production Streamlit apps are viable

**Consider React/Next.js if:**
- Need complex, real-time UI interactions
- Building a consumer-facing product at scale
- Want native mobile app (React Native)
- Need fine-grained UI/UX control
- Hiring frontend developers

**Current recommendation**: Stay with Python/Streamlit for at least 12-18 months. Focus on backend skills, database design, and API development first.

### Success Metrics

**Technical:**
- API response time < 500ms (cached)
- 99% uptime
- <2s page load time
- Test coverage > 80%

**User:**
- 100+ active users/month
- 50+ saved comparisons/week
- <5% bounce rate
- User feedback score > 4/5

### Next Immediate Steps

1. **Implement quick performance wins** (Week 1-2)
   - Add `@st.cache_data` to TfL calls
   - Use `st.fragment()` for dynamic sections

2. **Start SQL learning** (Week 3-4)
   - Complete PostgreSQL tutorial
   - Design initial database schema

3. **Prototype FastAPI backend** (Month 2)
   - Create simple API endpoint
   - Connect to local PostgreSQL
   - Test with Streamlit

4. **Plan database migration** (Month 3)
   - Schema for users, comparisons, cached_journeys
   - Migration strategy from session state
