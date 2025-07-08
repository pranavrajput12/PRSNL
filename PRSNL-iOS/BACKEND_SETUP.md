# PRSNL Backend Setup Guide

This guide provides instructions for setting up a minimal backend server to test the PRSNL iOS app with online functionality.

## Quick Start Backend Server

Below is a minimal Express.js server implementation that provides the basic API endpoints needed for the PRSNL app. This server stores data in memory, so it's suitable for testing but not for production use.

### Prerequisites
- Node.js 16.x or later
- npm or yarn package manager

### Setup Instructions

1. **Create a New Directory for the Server**
   ```bash
   mkdir prsnl-backend
   cd prsnl-backend
   ```

2. **Initialize the Project**
   ```bash
   npm init -y
   ```

3. **Install Dependencies**
   ```bash
   npm install express cors body-parser uuid
   ```

4. **Create the Server File**
   Create a file named `server.js` with the following content:

   ```javascript
   const express = require('express');
   const cors = require('cors');
   const bodyParser = require('body-parser');
   const { v4: uuidv4 } = require('uuid');

   const app = express();
   const port = 8000;

   // Middleware
   app.use(cors());
   app.use(bodyParser.json());

   // API key validation middleware
   const validateApiKey = (req, res, next) => {
     const apiKey = req.headers['x-api-key'];
     if (!apiKey) {
       return res.status(401).json({ error: 'API key is required' });
     }
     if (apiKey !== 'test-api-key-for-development') {
       return res.status(403).json({ error: 'Invalid API key' });
     }
     next();
   };

   // In-memory data store
   const items = [];
   const tags = ['work', 'personal', 'research', 'ideas', 'important'];

   // Generate some initial items
   for (let i = 1; i <= 20; i++) {
     items.push({
       id: uuidv4(),
       title: `Test Item ${i}`,
       content: `This is the content for test item ${i}. It contains some text that would typically be stored in a knowledge base.`,
       url: i % 3 === 0 ? `https://example.com/article${i}` : null,
       summary: i % 4 === 0 ? `Summary for item ${i}` : null,
       status: 'active',
       createdAt: new Date(Date.now() - i * 86400000).toISOString(),
       updatedAt: new Date(Date.now() - i * 43200000).toISOString(),
       accessCount: Math.floor(Math.random() * 10),
       accessedAt: new Date(Date.now() - i * 21600000).toISOString(),
       tags: tags.slice(0, Math.floor(Math.random() * tags.length)),
       itemType: ['note', 'article', 'video', 'document', 'image', 'audio'][Math.floor(Math.random() * 6)],
       attachments: i % 5 === 0 ? [
         {
           id: uuidv4(),
           fileType: 'image/jpeg',
           filePath: `https://picsum.photos/id/${i * 10}/200/300`,
           mimeType: 'image/jpeg',
           metadata: {
             alt: `Image for item ${i}`,
             title: `Attachment ${i}`,
             isRemote: true
           }
         }
       ] : []
     });
   }

   // API Routes

   // Get timeline
   app.get('/api/timeline', validateApiKey, (req, res) => {
     const page = parseInt(req.query.page) || 1;
     const limit = parseInt(req.query.limit) || 10;
     const startIndex = (page - 1) * limit;
     const endIndex = page * limit;

     const selectedTags = req.query.tags ? req.query.tags.split(',') : [];
     
     let filteredItems = [...items];
     
     // Filter by tags if provided
     if (selectedTags.length > 0) {
       filteredItems = filteredItems.filter(item => 
         selectedTags.some(tag => item.tags.includes(tag))
       );
     }
     
     // Sort by updatedAt (newest first)
     filteredItems.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
     
     // Paginate
     const paginatedItems = filteredItems.slice(startIndex, endIndex);
     
     res.json({
       items: paginatedItems,
       totalResults: filteredItems.length
     });
   });

   // Search items
   app.get('/api/search', validateApiKey, (req, res) => {
     const query = req.query.q || '';
     const page = parseInt(req.query.page) || 1;
     const limit = parseInt(req.query.limit) || 10;
     const startIndex = (page - 1) * limit;
     const endIndex = page * limit;
     
     if (!query) {
       return res.status(400).json({ error: 'Search query is required' });
     }
     
     // Perform search
     const searchResults = items.filter(item => 
       item.title.toLowerCase().includes(query.toLowerCase()) || 
       item.content.toLowerCase().includes(query.toLowerCase()) ||
       item.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
     );
     
     // Sort by relevance (simple implementation - title matches first)
     searchResults.sort((a, b) => {
       const aInTitle = a.title.toLowerCase().includes(query.toLowerCase());
       const bInTitle = b.title.toLowerCase().includes(query.toLowerCase());
       
       if (aInTitle && !bInTitle) return -1;
       if (!aInTitle && bInTitle) return 1;
       
       // If tie, sort by updated date
       return new Date(b.updatedAt) - new Date(a.updatedAt);
     });
     
     // Paginate
     const paginatedResults = searchResults.slice(startIndex, endIndex);
     
     res.json({
       items: paginatedResults,
       totalResults: searchResults.length
     });
   });

   // Get item by ID
   app.get('/api/items/:id', validateApiKey, (req, res) => {
     const item = items.find(i => i.id === req.params.id);
     
     if (!item) {
       return res.status(404).json({ error: 'Item not found' });
     }
     
     // Update access count
     item.accessCount += 1;
     item.accessedAt = new Date().toISOString();
     
     res.json(item);
   });

   // Create new item
   app.post('/api/items', validateApiKey, (req, res) => {
     const { title, content, url, tags, itemType } = req.body;
     
     if (!title || (!content && !url)) {
       return res.status(400).json({ error: 'Title and either content or URL are required' });
     }
     
     const newItem = {
       id: uuidv4(),
       title,
       content: content || '',
       url: url || null,
       summary: null,
       status: 'active',
       createdAt: new Date().toISOString(),
       updatedAt: new Date().toISOString(),
       accessCount: 0,
       accessedAt: null,
       tags: tags || [],
       itemType: itemType || 'note',
       attachments: []
     };
     
     items.push(newItem);
     
     res.status(201).json(newItem);
   });

   // Get all tags
   app.get('/api/tags', validateApiKey, (req, res) => {
     // Get unique tags from all items
     const allTags = new Set();
     items.forEach(item => {
       item.tags.forEach(tag => allTags.add(tag));
     });
     
     res.json(Array.from(allTags).sort());
   });

   // Update item
   app.put('/api/items/:id', validateApiKey, (req, res) => {
     const itemIndex = items.findIndex(i => i.id === req.params.id);
     
     if (itemIndex === -1) {
       return res.status(404).json({ error: 'Item not found' });
     }
     
     const updatedItem = {
       ...items[itemIndex],
       ...req.body,
       updatedAt: new Date().toISOString()
     };
     
     items[itemIndex] = updatedItem;
     
     res.json(updatedItem);
   });

   // Delete item
   app.delete('/api/items/:id', validateApiKey, (req, res) => {
     const itemIndex = items.findIndex(i => i.id === req.params.id);
     
     if (itemIndex === -1) {
       return res.status(404).json({ error: 'Item not found' });
     }
     
     items.splice(itemIndex, 1);
     
     res.status(204).send();
   });

   // Server health check
   app.get('/api/health', (req, res) => {
     res.json({ status: 'ok', timestamp: new Date().toISOString() });
   });

   // Start the server
   app.listen(port, () => {
     console.log(`PRSNL Backend running at http://localhost:${port}`);
     console.log(`API is available at http://localhost:${port}/api`);
     console.log(`Use API key 'test-api-key-for-development' for testing`);
   });
   ```

5. **Start the Server**
   ```bash
   node server.js
   ```

6. **Server is Now Running**
   - The server runs at http://localhost:8000
   - API endpoint: http://localhost:8000/api
   - API key: `test-api-key-for-development`

## Configuring the iOS App to Use Your Server

1. Open the PRSNL iOS app on your device
2. Go to Settings
3. Set the server URL to `http://YOUR_COMPUTER_IP:8000/api`
   - Replace YOUR_COMPUTER_IP with your local IP address (e.g., 192.168.1.10)
   - Make sure your phone and computer are on the same network
4. Enter the API key: `test-api-key-for-development`
5. Click "Test Connection" to verify

## Testing Offline Functionality

To test offline functionality:

1. **Connect to the server** and load some data (browse the Timeline and Search)
2. **Disconnect from Wi-Fi** on your phone or turn on Airplane Mode
3. **Use the app** - you should see offline indicators, but still be able to view cached data
4. **Make changes** - these will be stored locally
5. **Reconnect to Wi-Fi** - the app should automatically sync with the server

## Extending the Backend

This minimal implementation can be extended with:

- **Database persistence** - Add MongoDB or SQLite to store data permanently
- **File uploads** - Add multer middleware to handle attachment uploads
- **Authentication** - Implement proper user authentication
- **Environment variables** - Move API key and configuration to environment variables

## Troubleshooting

- **Connection issues**: Ensure your phone and computer are on the same network
- **API errors**: Check the server console logs for error details
- **Cannot reach server**: Verify your computer's firewall isn't blocking the connection