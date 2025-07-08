# PRSNL iOS App: Database Communication Architecture

This document explains in detail how the PRSNL iOS app communicates with both the remote database (server) and local database (Core Data).

## Architecture Overview

The PRSNL iOS app uses a sophisticated "online-first with offline fallback" architecture that enables seamless operation regardless of network connectivity. This document explains the data flow, components, and synchronization mechanisms implemented in the app.

```
┌─────────────────────────────────────┐          ┌───────────────────────────┐
│             iOS Device              │          │        Remote Server       │
│                                     │          │                           │
│ ┌─────────────┐     ┌─────────────┐ │          │ ┌─────────────────────┐   │
│ │    Views    │     │ ViewModels  │ │  HTTP/S  │ │                     │   │
│ │  (SwiftUI)  │◄───►│ (MVVM)      │◄┼──────────┼►│    REST API         │   │
│ └─────────────┘     └──────┬──────┘ │  JSON    │ │                     │   │
│                            │        │          │ └─────────┬───────────┘   │
│                            ▼        │          │           │               │
│ ┌────────────────┐  ┌─────────────┐ │          │ ┌─────────▼───────────┐   │
│ │ NetworkMonitor │  │ SyncManager │ │          │ │                     │   │
│ │ (Connectivity) │  │             │ │          │ │  Server Database    │   │
│ └────────────────┘  └──────┬──────┘ │          │ │                     │   │
│                            │        │          │ └─────────────────────┘   │
│                            ▼        │          │                           │
│ ┌─────────────────────────────────┐ │          └───────────────────────────┘
│ │         CoreDataManager         │ │
│ └──────────────┬──────────────────┘ │
│                │                    │
│                ▼                    │
│ ┌─────────────────────────────────┐ │
│ │         Core Data               │ │
│ │  ┌─────────┐ ┌─────────┐        │ │
│ │  │ CDItem  │ │ CDTag   │        │ │
│ │  └─────────┘ └─────────┘        │ │
│ └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

## Key Components

### 1. **User Interface Layer**
- **SwiftUI Views**
  - Present data to the user
  - Capture user input
  - Display connectivity status
  - Show sync indicators

### 2. **Application Logic Layer**
- **ViewModels**
  - Implement MVVM pattern
  - Coordinate between views and data sources
  - Handle business logic
  - Examples: `TimelineViewModel`, `SearchViewModel`

### 3. **Network Layer**
- **APIClient**
  - Handles all HTTP communication with the server
  - Uses URLSession with async/await
  - Performs API requests (GET, POST, PUT, DELETE)
  - Converts between JSON and Swift models

- **NetworkMonitor**
  - Monitors network connectivity status
  - Publishes network status changes
  - Triggers sync when connectivity is restored

### 4. **Synchronization Layer**
- **SyncManager**
  - Orchestrates bidirectional sync between local and remote data
  - Maintains sync state for each item
  - Resolves conflicts
  - Handles the sync queue
  - Provides sync status updates via Combine publisher

### 5. **Persistence Layer**
- **CoreDataManager**
  - Manages Core Data operations
  - Converts between Core Data entities and Swift models
  - Handles CRUD operations on the local database
  - Provides search functionality for offline use

- **Core Data Stack**
  - Local database using Core Data
  - Entities: CDItem, CDTag, CDAttachment
  - Relationships and cascade rules
  - Persistent storage

## Data Flow

### Online Mode (Normal Operation)

1. **Reading Data**:
   ```
   Server Database → REST API → APIClient → ViewModel → SwiftUI Views
                                  ↓
                            CoreDataManager → Core Data (cache)
   ```

2. **Writing Data**:
   ```
   SwiftUI Views → ViewModel → APIClient → REST API → Server Database
                       ↓
                 CoreDataManager → Core Data (cache)
   ```

### Offline Mode (No Connectivity)

1. **Reading Data**:
   ```
   Core Data → CoreDataManager → ViewModel → SwiftUI Views
   ```

2. **Writing Data**:
   ```
   SwiftUI Views → ViewModel → CoreDataManager → Core Data
                                     ↓
                                  Mark as "needsUpload"
   ```

### Synchronization Process

When connectivity is restored:

```
SyncManager → CoreDataManager → Fetch items marked for sync
      ↓
APIClient → Send changes to server
      ↓
APIClient → Fetch latest data from server
      ↓
CoreDataManager → Update local database
      ↓
ViewModel → Update UI
```

## SyncStatus Tracking

Each item in Core Data has a `syncStatus` property that can be one of:

- **Synced**: Item is in sync with the server
- **NeedsUpload**: Item has local changes that need to be pushed to server
- **NeedsDeletion**: Item has been deleted locally and needs to be deleted on server

## Conflict Resolution

The app implements a simple "server wins" conflict resolution strategy:

1. Local changes are attempted to be pushed to the server
2. If the server rejects the change (e.g., due to a concurrent modification):
   - The server version is downloaded
   - Local changes are discarded
   - The UI is updated with the server version

## Network Connectivity Management

The NetworkMonitor component:
- Uses NWPathMonitor to detect network status changes
- Publishes connectivity status to interested components
- Automatically triggers sync when connectivity is restored
- Updates UI elements to show current connectivity status

## Implementation Details

### Core Data Model

The Core Data model includes:

- **CDItem**: Represents knowledge base items
  - Properties: id, title, content, url, tags, syncStatus, etc.
  - Relationships: tags (many-to-many), attachments (one-to-many)

- **CDTag**: Represents item tags
  - Properties: name
  - Relationships: items (many-to-many)

- **CDAttachment**: Represents file attachments
  - Properties: id, fileType, filePath, etc.
  - Relationships: item (many-to-one)

### Key Classes and Their Roles

- **SyncManager**: Orchestrates synchronization
  - Monitors network connectivity
  - Pushes local changes to server
  - Pulls remote changes to local database
  - Resolves conflicts
  - Publishes sync status updates

- **CoreDataManager**: Manages persistent storage
  - Handles CRUD operations
  - Converts between Core Data entities and Swift models
  - Provides search and query capabilities
  - Manages Core Data stack

- **APIClient**: Handles network communication
  - Performs HTTP requests
  - Handles authentication
  - Parses JSON responses
  - Handles network errors

## Conclusion

The PRSNL iOS app's database communication architecture provides:

1. **Seamless Online/Offline Experience**: Users can use the app regardless of connectivity
2. **Data Integrity**: Changes are synchronized between devices and server
3. **Performance**: Local data access for speed, remote sync for persistence
4. **Resilience**: Works even in unstable network conditions
5. **Scalability**: Architecture can handle growing data volume and complexity