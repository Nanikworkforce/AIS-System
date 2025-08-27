# AI System - Vercel Deployment Guide

## 🚀 Deployment Structure

Your AI System is now properly configured for Vercel deployment with:

### Frontend (`/frontend/`)
- **Landing Page**: `index.html` - Main entry point with navigation
- **Real-time Dashboard**: `realtime_dashboard.html` - Live vessel tracking
- **Vessel Categorization**: `vessel_categorization_dashboard.html` - Vessel analytics
- **Package Configuration**: `package.json` - Frontend dependencies

### Backend API (`/api/`)
- **Serverless Function**: `index.py` - Vercel-compatible Flask API wrapper
- **Original Backend**: Located in `/backend/` folder
- **Dependencies**: `requirements.txt` - Python packages

## 🔧 Configuration Files

### `vercel.json`
- Configures static frontend serving
- Sets up Python serverless function for API
- Defines routing for proper URL handling

### `.vercelignore` 
- Excludes development files from deployment
- Keeps deployment package size minimal

## 📝 Deployment Steps

1. **Connect to Vercel**:
   ```bash
   npm i -g vercel
   vercel login
   ```

2. **Deploy**:
   ```bash
   vercel --prod
   ```

3. **Update WebSocket URLs**:
   After deployment, update the WebSocket URLs in:
   - `frontend/realtime_dashboard.html` (line 372-374)
   - `frontend/vessel_categorization_dashboard.html` (line 636-638)
   
   Replace `'wss://your-backend-domain.com'` with your actual Vercel domain.

## 🌐 URL Structure After Deployment

- **Homepage**: `https://your-app.vercel.app/`
- **Real-time Dashboard**: `https://your-app.vercel.app/realtime_dashboard.html`
- **Vessel Dashboard**: `https://your-app.vercel.app/vessel_categorization_dashboard.html`
- **API Endpoints**: `https://your-app.vercel.app/api/*`

## ⚡ Features Deployed

✅ Static frontend with modern UI  
✅ Flask API as serverless function  
✅ Proper routing configuration  
✅ CORS enabled for frontend-backend communication  
✅ Environment-based WebSocket URL detection  
✅ Responsive design for mobile/desktop  

## 🔍 Troubleshooting

### 404 Errors
- Ensure `vercel.json` routes are properly configured
- Check that `frontend/index.html` exists and is accessible
- Verify file paths in routing configuration

### API Issues
- Check Python dependencies in `requirements.txt`
- Ensure `api/index.py` imports are working
- Monitor Vercel function logs for errors

### WebSocket Connections
- For production, you'll need a separate WebSocket server
- Consider using Vercel's Edge Functions or external WebSocket service
- Update WebSocket URLs after deploying backend WebSocket server

## 📊 Performance Notes

- Frontend is served as static files (fast CDN delivery)
- Backend API runs as serverless functions (scales automatically)
- Fleet size reduced to 500 vessels for better serverless performance
- Consider implementing database persistence for production use

## 🔗 Next Steps

1. Deploy the application to Vercel
2. Set up a dedicated WebSocket server for real-time features
3. Configure environment variables for production
4. Add monitoring and analytics
5. Implement user authentication if needed
