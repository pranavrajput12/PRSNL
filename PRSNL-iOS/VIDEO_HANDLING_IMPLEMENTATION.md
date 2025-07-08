# PRSNL iOS: Video Content Handling Implementation

This document outlines the comprehensive implementation plan for adding video content support to the PRSNL iOS app, building on the existing attachment infrastructure.

## 1. Overview

Video content handling will enable users to:
- Upload videos from their device camera or library
- Capture videos directly within the app
- View video thumbnails in the Timeline and Search views
- Play videos within the app
- Store videos efficiently both locally and remotely
- Maintain video support while offline

## 2. Backend Requirements

The current Express.js backend will need extensions to handle video uploads and processing:

### 2.1 API Endpoints

Add these endpoints to `server.js`:

```javascript
// Upload video attachment
app.post('/api/items/:id/attachments/video', validateApiKey, upload.single('video'), async (req, res) => {
  try {
    const itemId = req.params.id;
    const item = items.find(i => i.id === itemId);
    
    if (!item) {
      return res.status(404).json({ error: 'Item not found' });
    }
    
    // Create video attachment
    const videoAttachment = {
      id: uuidv4(),
      fileType: 'video',
      filePath: `/videos/${req.file.filename}`,
      mimeType: req.file.mimetype,
      metadata: {
        title: req.body.title || 'Video Attachment',
        duration: req.body.duration || 0,
        thumbnail: `/thumbnails/${req.file.filename.replace(/\.[^/.]+$/, '.jpg')}`,
        width: req.body.width || 0,
        height: req.body.height || 0,
        isRemote: false
      }
    };
    
    // Create thumbnail (implementation depends on server capabilities)
    await generateThumbnail(req.file.path, videoAttachment.metadata.thumbnail);
    
    // Add attachment to item
    item.attachments.push(videoAttachment);
    item.updatedAt = new Date().toISOString();
    
    res.status(201).json(videoAttachment);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Stream video content
app.get('/api/videos/:filename', (req, res) => {
  const filename = req.params.filename;
  const videoPath = path.join(__dirname, 'media', 'videos', filename);
  
  // Check if file exists
  if (!fs.existsSync(videoPath)) {
    return res.status(404).json({ error: 'Video not found' });
  }
  
  // Get file stats
  const stat = fs.statSync(videoPath);
  const fileSize = stat.size;
  const range = req.headers.range;
  
  // Handle range requests for video streaming
  if (range) {
    const parts = range.replace(/bytes=/, '').split('-');
    const start = parseInt(parts[0], 10);
    const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
    const chunkSize = (end - start) + 1;
    const file = fs.createReadStream(videoPath, { start, end });
    
    const headers = {
      'Content-Range': `bytes ${start}-${end}/${fileSize}`,
      'Accept-Ranges': 'bytes',
      'Content-Length': chunkSize,
      'Content-Type': 'video/mp4'
    };
    
    res.writeHead(206, headers);
    file.pipe(res);
  } else {
    // No range requested, send entire file
    const headers = {
      'Content-Length': fileSize,
      'Content-Type': 'video/mp4'
    };
    
    res.writeHead(200, headers);
    fs.createReadStream(videoPath).pipe(res);
  }
});
```

### 2.2 Video Processing

Install necessary dependencies:

```bash
npm install multer ffmpeg-static fluent-ffmpeg
```

Add video processing utilities:

```javascript
const ffmpeg = require('fluent-ffmpeg');
const ffmpegPath = require('ffmpeg-static');
ffmpeg.setFfmpegPath(ffmpegPath);

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    if (file.mimetype.startsWith('video/')) {
      cb(null, './media/videos');
    } else if (file.mimetype.startsWith('image/')) {
      cb(null, './media/images');
    } else {
      cb(null, './media/files');
    }
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ storage: storage });

// Generate thumbnail from video
async function generateThumbnail(videoPath, thumbnailPath) {
  return new Promise((resolve, reject) => {
    ffmpeg(videoPath)
      .screenshots({
        timestamps: ['10%'],
        filename: path.basename(thumbnailPath),
        folder: path.dirname(thumbnailPath),
        size: '320x240'
      })
      .on('end', () => resolve())
      .on('error', (err) => reject(err));
  });
}
```

## 3. iOS Implementation

### 3.1 Model Updates

Update the `Attachment` model in `ItemModel.swift`:

```swift
// Add video-specific properties
struct AttachmentMetadata: Codable {
    let title: String?
    let alt: String?
    let isRemote: Bool
    let thumbnail: String?  // Path to thumbnail for videos
    let duration: Double?   // Video duration in seconds
    let width: Int?         // Video width
    let height: Int?        // Video height
}
```

### 3.2 Core Data Updates

Update the Core Data model (`PRSNLModel.xcdatamodeld`) to include video-specific attributes:

```swift
// Add to CDAttachment entity
entity.addAttribute(NSAttributeDescription().with {
    $0.name = "videoThumbnailPath"
    $0.attributeType = .stringAttributeType
    $0.isOptional = true
})

entity.addAttribute(NSAttributeDescription().with {
    $0.name = "videoDuration"
    $0.attributeType = .doubleAttributeType
    $0.isOptional = true
})

entity.addAttribute(NSAttributeDescription().with {
    $0.name = "videoWidth"
    $0.attributeType = .integer32AttributeType
    $0.isOptional = true
})

entity.addAttribute(NSAttributeDescription().with {
    $0.name = "videoHeight"
    $0.attributeType = .integer32AttributeType
    $0.isOptional = true
})
```

### 3.3 API Client Updates

Add video upload methods to `APIClient.swift`:

```swift
/// Uploads a video attachment to an existing item
/// - Parameters:
///   - itemId: The ID of the item to attach the video to
///   - videoURL: Local URL of the video file
///   - metadata: Additional metadata about the video
/// - Returns: The created attachment
func uploadVideoAttachment(itemId: String, videoURL: URL, metadata: [String: Any]) async throws -> Attachment {
    guard let serverURL = URL(string: baseURL),
          let apiKey = try? KeychainService.shared.getAPIKey() else {
        throw APIError.invalidConfiguration
    }
    
    let endpoint = serverURL.appendingPathComponent("items/\(itemId)/attachments/video")
    var request = URLRequest(url: endpoint)
    request.httpMethod = "POST"
    request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
    
    // Generate boundary string
    let boundary = UUID().uuidString
    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
    
    // Create multipart form data
    var data = Data()
    
    // Add metadata fields
    for (key, value) in metadata {
        data.append("--\(boundary)\r\n".data(using: .utf8)!)
        data.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
        data.append("\(value)\r\n".data(using: .utf8)!)
    }
    
    // Add video file
    data.append("--\(boundary)\r\n".data(using: .utf8)!)
    data.append("Content-Disposition: form-data; name=\"video\"; filename=\"\(videoURL.lastPathComponent)\"\r\n".data(using: .utf8)!)
    data.append("Content-Type: video/mp4\r\n\r\n".data(using: .utf8)!)
    
    do {
        let videoData = try Data(contentsOf: videoURL)
        data.append(videoData)
        data.append("\r\n".data(using: .utf8)!)
    } catch {
        throw APIError.invalidData
    }
    
    // Add final boundary
    data.append("--\(boundary)--\r\n".data(using: .utf8)!)
    
    // Upload the data
    let (responseData, response) = try await URLSession.shared.upload(for: request, from: data)
    
    guard let httpResponse = response as? HTTPURLResponse else {
        throw APIError.invalidResponse
    }
    
    if httpResponse.statusCode >= 400 {
        throw APIError.serverError(statusCode: httpResponse.statusCode)
    }
    
    // Decode response
    let attachment = try JSONDecoder().decode(Attachment.self, from: responseData)
    return attachment
}

/// Gets a streaming URL for a video attachment
/// - Parameter attachment: The video attachment
/// - Returns: A URL that can be used for streaming
func getVideoStreamingURL(for attachment: Attachment) -> URL? {
    guard let serverURL = URL(string: baseURL) else {
        return nil
    }
    
    if attachment.metadata?.isRemote == true, let path = attachment.filePath {
        // For remote videos, return the full URL
        return URL(string: path)
    } else if let path = attachment.filePath {
        // For local videos, construct server URL
        return serverURL.deletingLastPathComponent().appendingPathComponent(path)
    }
    
    return nil
}
```

### 3.4 Video Picker Component

Create a new file: `PRSNL-iOS/Implementation/PRSNL/Features/Capture/VideoPickerView.swift`

```swift
import SwiftUI
import PhotosUI
import AVKit

struct VideoPickerView: View {
    @Binding var selectedVideoURL: URL?
    @Binding var thumbnailImage: UIImage?
    @State private var isPickerPresented = false
    @State private var sourceType: UIImagePickerController.SourceType?
    
    var body: some View {
        VStack {
            if let thumbnailImage = thumbnailImage {
                ZStack {
                    Image(uiImage: thumbnailImage)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(height: 200)
                        .cornerRadius(8)
                        .clipped()
                    
                    // Play button overlay
                    Circle()
                        .fill(Color.black.opacity(0.6))
                        .frame(width: 50, height: 50)
                    
                    Image(systemName: "play.fill")
                        .foregroundColor(.white)
                        .font(.title2)
                }
                .onTapGesture {
                    if let url = selectedVideoURL {
                        let player = AVPlayer(url: url)
                        let playerController = AVPlayerViewController()
                        playerController.player = player
                        
                        // Present the player
                        let scenes = UIApplication.shared.connectedScenes
                        if let windowScene = scenes.first as? UIWindowScene,
                           let window = windowScene.windows.first,
                           let rootVC = window.rootViewController {
                            rootVC.present(playerController, animated: true) {
                                player.play()
                            }
                        }
                    }
                }
            } else {
                HStack {
                    Button(action: {
                        sourceType = .camera
                        isPickerPresented = true
                    }) {
                        VStack {
                            Image(systemName: "video.fill")
                                .font(.largeTitle)
                            Text("Record Video")
                                .font(.caption)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color(.systemGray6))
                        .cornerRadius(8)
                    }
                    
                    Button(action: {
                        sourceType = .photoLibrary
                        isPickerPresented = true
                    }) {
                        VStack {
                            Image(systemName: "photo.on.rectangle")
                                .font(.largeTitle)
                            Text("Choose Video")
                                .font(.caption)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color(.systemGray6))
                        .cornerRadius(8)
                    }
                }
            }
        }
        .sheet(isPresented: $isPickerPresented) {
            if let sourceType = sourceType {
                VideoPicker(selectedVideoURL: $selectedVideoURL, thumbnailImage: $thumbnailImage, sourceType: sourceType)
            }
        }
    }
}

struct VideoPicker: UIViewControllerRepresentable {
    @Binding var selectedVideoURL: URL?
    @Binding var thumbnailImage: UIImage?
    let sourceType: UIImagePickerController.SourceType
    @Environment(\.presentationMode) var presentationMode
    
    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.delegate = context.coordinator
        picker.sourceType = sourceType
        picker.mediaTypes = ["public.movie"]
        picker.videoQuality = .typeHigh
        picker.allowsEditing = true
        return picker
    }
    
    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, UINavigationControllerDelegate, UIImagePickerControllerDelegate {
        let parent: VideoPicker
        
        init(_ parent: VideoPicker) {
            self.parent = parent
        }
        
        func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
            if let videoURL = info[.mediaURL] as? URL {
                parent.selectedVideoURL = videoURL
                
                // Generate thumbnail
                generateThumbnail(from: videoURL) { [weak self] image in
                    DispatchQueue.main.async {
                        self?.parent.thumbnailImage = image
                    }
                }
            }
            
            parent.presentationMode.wrappedValue.dismiss()
        }
        
        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.presentationMode.wrappedValue.dismiss()
        }
        
        private func generateThumbnail(from videoURL: URL, completion: @escaping (UIImage?) -> Void) {
            let asset = AVAsset(url: videoURL)
            let imageGenerator = AVAssetImageGenerator(asset: asset)
            imageGenerator.appliesPreferredTrackTransform = true
            
            // Get thumbnail at 1 second
            let time = CMTime(seconds: 1, preferredTimescale: 60)
            
            imageGenerator.generateCGImagesAsynchronously(forTimes: [NSValue(time: time)]) { _, cgImage, _, _, _ in
                if let cgImage = cgImage {
                    let thumbnail = UIImage(cgImage: cgImage)
                    completion(thumbnail)
                } else {
                    completion(nil)
                }
            }
        }
    }
}
```

### 3.5 Video Player Component

Create a new file: `PRSNL-iOS/Implementation/PRSNL/Features/ItemDetail/VideoPlayerView.swift`

```swift
import SwiftUI
import AVKit

struct VideoPlayerView: View {
    let url: URL
    let title: String?
    
    @State private var player: AVPlayer?
    @State private var isPlaying = false
    @State private var isMuted = false
    @State private var isFullScreen = false
    @State private var playbackTime: Double = 0
    @State private var duration: Double = 0
    
    private let progressTimer = Timer.publish(every: 0.5, on: .main, in: .common).autoconnect()
    
    var body: some View {
        VStack(alignment: .leading) {
            if let title = title {
                Text(title)
                    .font(.headline)
                    .padding(.bottom, 4)
            }
            
            ZStack {
                // Video player
                VideoPlayer(player: player)
                    .aspectRatio(16/9, contentMode: .fit)
                    .cornerRadius(8)
                    .onAppear {
                        player = AVPlayer(url: url)
                        setupPlayer()
                    }
                    .onDisappear {
                        player?.pause()
                        player = nil
                    }
                
                // Custom overlay controls (optional)
                if !isFullScreen {
                    HStack {
                        Button(action: {
                            if isPlaying {
                                player?.pause()
                            } else {
                                player?.play()
                            }
                            isPlaying.toggle()
                        }) {
                            Image(systemName: isPlaying ? "pause.fill" : "play.fill")
                                .font(.title)
                                .foregroundColor(.white)
                                .padding(8)
                                .background(Color.black.opacity(0.5))
                                .clipShape(Circle())
                        }
                        
                        Spacer()
                        
                        Button(action: {
                            player?.isMuted.toggle()
                            isMuted.toggle()
                        }) {
                            Image(systemName: isMuted ? "speaker.slash.fill" : "speaker.wave.2.fill")
                                .font(.title)
                                .foregroundColor(.white)
                                .padding(8)
                                .background(Color.black.opacity(0.5))
                                .clipShape(Circle())
                        }
                        
                        Button(action: {
                            // Enter full screen mode
                            isFullScreen = true
                            
                            // Present full screen player
                            let playerController = AVPlayerViewController()
                            playerController.player = player
                            
                            let scenes = UIApplication.shared.connectedScenes
                            if let windowScene = scenes.first as? UIWindowScene,
                               let window = windowScene.windows.first,
                               let rootVC = window.rootViewController {
                                rootVC.present(playerController, animated: true) {
                                    player?.play()
                                    isPlaying = true
                                }
                                
                                // Add observer for dismissal
                                NotificationCenter.default.addObserver(forName: .AVPlayerViewControllerDismissedNotification, object: nil, queue: .main) { _ in
                                    isFullScreen = false
                                }
                            }
                        }) {
                            Image(systemName: "arrow.up.left.and.arrow.down.right")
                                .font(.title)
                                .foregroundColor(.white)
                                .padding(8)
                                .background(Color.black.opacity(0.5))
                                .clipShape(Circle())
                        }
                    }
                    .padding()
                }
            }
            
            // Progress bar
            if duration > 0 {
                VStack(spacing: 4) {
                    Slider(value: $playbackTime, in: 0...duration) { editing in
                        if !editing {
                            player?.seek(to: CMTime(seconds: playbackTime, preferredTimescale: 600))
                        }
                    }
                    
                    HStack {
                        Text(formatTime(playbackTime))
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Spacer()
                        
                        Text(formatTime(duration))
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding(.vertical)
        .onReceive(progressTimer) { _ in
            guard let player = player, isPlaying else { return }
            
            playbackTime = player.currentTime().seconds
            
            if player.currentItem?.status == .readyToPlay {
                duration = player.currentItem?.duration.seconds ?? 0
            }
        }
    }
    
    private func setupPlayer() {
        // Get duration when ready
        player?.currentItem?.addObserver(self, forKeyPath: "duration", options: [.new, .initial], context: nil)
        
        // Setup playback finished notification
        NotificationCenter.default.addObserver(
            forName: .AVPlayerItemDidPlayToEndTime,
            object: player?.currentItem,
            queue: .main
        ) { _ in
            isPlaying = false
            player?.seek(to: .zero)
        }
    }
    
    override func observeValue(forKeyPath keyPath: String?, of object: Any?, change: [NSKeyValueChangeKey : Any]?, context: UnsafeMutableRawPointer?) {
        if keyPath == "duration", let playerItem = object as? AVPlayerItem {
            duration = playerItem.duration.seconds
        }
    }
    
    private func formatTime(_ seconds: Double) -> String {
        let formatter = DateComponentsFormatter()
        formatter.allowedUnits = seconds >= 3600 ? [.hour, .minute, .second] : [.minute, .second]
        formatter.unitsStyle = .positional
        formatter.zeroFormattingBehavior = .pad
        
        return formatter.string(from: seconds) ?? "0:00"
    }
}
```

### 3.6 Integration with Capture Feature

Update `CaptureViewModel.swift` to support video uploads:

```swift
class CaptureViewModel: ObservableObject {
    // Add these properties
    @Published var selectedVideoURL: URL?
    @Published var videoThumbnail: UIImage?
    @Published var isUploading = false
    @Published var uploadProgress: Double = 0
    
    // Add this method
    func captureWithVideo(title: String, content: String, tags: [String], itemType: ItemType = .note) async throws -> Item {
        guard let videoURL = selectedVideoURL else {
            throw NSError(
                domain: "CaptureViewModel",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "No video selected"]
            )
        }
        
        // First create the item
        let item = try await APIClient.shared.createItem(
            title: title,
            content: content,
            tags: tags,
            itemType: itemType
        )
        
        // Then upload the video attachment
        let asset = AVAsset(url: videoURL)
        let videoTrack = try await asset.loadTracks(withMediaType: .video).first
        
        let size = try await videoTrack?.load(.naturalSize) ?? CGSize(width: 0, height: 0)
        let duration = try await asset.load(.duration).seconds
        
        let metadata: [String: Any] = [
            "title": "\(title) Video",
            "duration": duration,
            "width": Int(size.width),
            "height": Int(size.height)
        ]
        
        _ = try await APIClient.shared.uploadVideoAttachment(
            itemId: item.id,
            videoURL: videoURL,
            metadata: metadata
        )
        
        return item
    }
}
```

Update `CaptureView.swift` to include video picker:

```swift
struct CaptureView: View {
    @StateObject private var viewModel = CaptureViewModel()
    @State private var showMediaPicker = false
    @State private var mediaType: MediaType = .none
    
    enum MediaType {
        case none, image, video
    }
    
    var body: some View {
        // Add this section to the form
        Section(header: Text("Media")) {
            HStack {
                Button(action: {
                    mediaType = .image
                    showMediaPicker = true
                }) {
                    HStack {
                        Image(systemName: "photo")
                        Text("Add Image")
                    }
                }
                
                Divider()
                
                Button(action: {
                    mediaType = .video
                    showMediaPicker = true
                }) {
                    HStack {
                        Image(systemName: "video")
                        Text("Add Video")
                    }
                }
            }
            .frame(maxWidth: .infinity)
            
            if mediaType == .video, viewModel.videoThumbnail != nil {
                VideoPickerView(
                    selectedVideoURL: $viewModel.selectedVideoURL,
                    thumbnailImage: $viewModel.videoThumbnail
                )
            }
        }
        .sheet(isPresented: $showMediaPicker) {
            if mediaType == .video {
                VideoPickerView(
                    selectedVideoURL: $viewModel.selectedVideoURL,
                    thumbnailImage: $viewModel.videoThumbnail
                )
            } else if mediaType == .image {
                // Existing image picker
            }
        }
    }
}
```

### 3.7 Integration with ItemDetailView

Update `ItemDetailView.swift` to handle video attachments:

```swift
struct ItemDetailView: View {
    let item: Item
    
    var body: some View {
        ScrollView {
            // Existing code...
            
            // Add this for attachment handling
            if let attachments = item.attachments, !attachments.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Attachments")
                        .font(.headline)
                    
                    ForEach(attachments) { attachment in
                        if attachment.fileType == "video/mp4" || attachment.mimeType?.contains("video/") == true {
                            if let url = APIClient.shared.getVideoStreamingURL(for: attachment) {
                                VideoPlayerView(
                                    url: url,
                                    title: attachment.metadata?.title ?? "Video"
                                )
                                .frame(height: 250)
                            }
                        } else if attachment.fileType == "image/jpeg" || attachment.mimeType?.contains("image/") == true {
                            // Existing image attachment code
                        }
                    }
                }
                .padding(.vertical)
            }
        }
    }
}
```

## 4. Core Data Integration

Update `CoreDataManager.swift` to handle video attachments:

```swift
func saveVideoAttachment(url: URL, forItem item: CDItem, in context: NSManagedObjectContext) throws -> CDAttachment {
    // Get video metadata
    let asset = AVAsset(url: url)
    
    // Create Core Data attachment
    let cdAttachment = CDAttachment(context: context)
    cdAttachment.id = UUID().uuidString
    cdAttachment.fileType = "video/mp4"
    cdAttachment.filePath = url.lastPathComponent
    cdAttachment.mimeType = "video/mp4"
    cdAttachment.item = item
    
    // Store video metadata
    do {
        if let videoTrack = try await asset.loadTracks(withMediaType: .video).first {
            let size = try await videoTrack.load(.naturalSize)
            let duration = try await asset.load(.duration).seconds
            
            cdAttachment.videoDuration = duration
            cdAttachment.videoWidth = Int32(size.width)
            cdAttachment.videoHeight = Int32(size.height)
            
            // Generate and save thumbnail
            let thumbnailURL = try await generateThumbnail(from: url)
            cdAttachment.videoThumbnailPath = thumbnailURL.lastPathComponent
        }
    } catch {
        print("Error getting video metadata: \(error)")
    }
    
    // Save to Core Data
    try saveContext(context)
    
    return cdAttachment
}

private func generateThumbnail(from videoURL: URL) async throws -> URL {
    return try await withCheckedThrowingContinuation { continuation in
        let asset = AVAsset(url: videoURL)
        let imageGenerator = AVAssetImageGenerator(asset: asset)
        imageGenerator.appliesPreferredTrackTransform = true
        
        let time = CMTime(seconds: 1, preferredTimescale: 60)
        
        imageGenerator.generateCGImagesAsynchronously(forTimes: [NSValue(time: time)]) { _, cgImage, _, _, error in
            if let error = error {
                continuation.resume(throwing: error)
                return
            }
            
            if let cgImage = cgImage, let uiImage = UIImage(cgImage: cgImage) {
                do {
                    // Create thumbnail file in app's documents directory
                    let fileManager = FileManager.default
                    let documentsDirectory = try fileManager.url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
                    let thumbnailName = videoURL.deletingPathExtension().lastPathComponent + "_thumbnail.jpg"
                    let thumbnailURL = documentsDirectory.appendingPathComponent(thumbnailName)
                    
                    // Convert UIImage to JPEG data
                    if let jpegData = uiImage.jpegData(compressionQuality: 0.8) {
                        try jpegData.write(to: thumbnailURL)
                        continuation.resume(returning: thumbnailURL)
                    } else {
                        throw NSError(domain: "CoreDataManager", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to create JPEG data"])
                    }
                } catch {
                    continuation.resume(throwing: error)
                }
            } else {
                continuation.resume(throwing: NSError(domain: "CoreDataManager", code: 2, userInfo: [NSLocalizedDescriptionKey: "Failed to generate thumbnail"]))
            }
        }
    }
}
```

## 5. Offline Video Handling

Update `SyncManager.swift` to handle video attachments during sync:

```swift
private func pushLocalChanges() async throws {
    // Existing code...
    
    // Handle video attachments specifically
    for item in itemsToSync {
        // Get attachments that need syncing
        let videoAttachments = item.attachments?.allObjects as? [CDAttachment] ?? []
        let videoAttachmentsToSync = videoAttachments.filter { $0.syncStatus == SyncStatus.needsUpload.rawValue && $0.mimeType?.contains("video/") == true }
        
        for attachment in videoAttachmentsToSync {
            if let filePath = attachment.filePath, let id = item.id {
                // Get file URL
                let fileManager = FileManager.default
                let documentsDirectory = try fileManager.url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: false)
                let fileURL = documentsDirectory.appendingPathComponent(filePath)
                
                // Upload to server
                if fileManager.fileExists(atPath: fileURL.path) {
                    let metadata: [String: Any] = [
                        "title": attachment.metadata ?? "Video",
                        "duration": attachment.videoDuration ?? 0,
                        "width": attachment.videoWidth ?? 0,
                        "height": attachment.videoHeight ?? 0
                    ]
                    
                    _ = try await APIClient.shared.uploadVideoAttachment(
                        itemId: id,
                        videoURL: fileURL,
                        metadata: metadata
                    )
                    
                    // Update sync status
                    attachment.syncStatus = SyncStatus.synced.rawValue
                }
            }
        }
    }
}
```

## 6. Performance Considerations

### 6.1 Video Optimization

For better performance, implement video compression before upload:

```swift
func compressVideo(inputURL: URL) async throws -> URL {
    return try await withCheckedThrowingContinuation { continuation in
        let outputURL = FileManager.default.temporaryDirectory.appendingPathComponent("compressed_\(UUID().uuidString).mp4")
        
        let exporter = AVAssetExportSession(asset: AVAsset(url: inputURL), presetName: AVAssetExportPresetMediumQuality)
        exporter?.outputURL = outputURL
        exporter?.outputFileType = .mp4
        
        exporter?.exportAsynchronously {
            if let error = exporter?.error {
                continuation.resume(throwing: error)
            } else if let outputURL = exporter?.outputURL {
                continuation.resume(returning: outputURL)
            } else {
                continuation.resume(throwing: NSError(domain: "VideoCompression", code: 1, userInfo: [NSLocalizedDescriptionKey: "Unknown compression error"]))
            }
        }
    }
}
```

### 6.2 Caching Strategy

Implement caching for video thumbnails and frequently accessed videos:

```swift
class VideoCacheManager {
    static let shared = VideoCacheManager()
    
    private let cache = NSCache<NSString, NSData>()
    private let fileManager = FileManager.default
    
    private init() {
        // Set cache limits
        cache.totalCostLimit = 50 * 1024 * 1024 // 50MB
    }
    
    func cacheVideoThumbnail(data: Data, for id: String) {
        cache.setObject(data as NSData, forKey: id as NSString)
    }
    
    func getVideoThumbnail(for id: String) -> Data? {
        return cache.object(forKey: id as NSString) as Data?
    }
    
    func cacheVideo(url: URL, forId id: String) throws {
        let cacheDirectory = try fileManager.url(for: .cachesDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
        let destinationURL = cacheDirectory.appendingPathComponent("\(id).mp4")
        
        if fileManager.fileExists(atPath: destinationURL.path) {
            try fileManager.removeItem(at: destinationURL)
        }
        
        try fileManager.copyItem(at: url, to: destinationURL)
    }
    
    func getCachedVideoURL(for id: String) -> URL? {
        do {
            let cacheDirectory = try fileManager.url(for: .cachesDirectory, in: .userDomainMask, appropriateFor: nil, create: false)
            let videoURL = cacheDirectory.appendingPathComponent("\(id).mp4")
            
            if fileManager.fileExists(atPath: videoURL.path) {
                return videoURL
            }
        } catch {
            print("Error accessing cache directory: \(error)")
        }
        
        return nil
    }
    
    func clearCache() {
        cache.removeAllObjects()
        
        do {
            let cacheDirectory = try fileManager.url(for: .cachesDirectory, in: .userDomainMask, appropriateFor: nil, create: false)
            let cacheFiles = try fileManager.contentsOfDirectory(at: cacheDirectory, includingPropertiesForKeys: nil)
            
            for file in cacheFiles where file.pathExtension == "mp4" {
                try fileManager.removeItem(at: file)
            }
        } catch {
            print("Error clearing video cache: \(error)")
        }
    }
}
```

## 7. Testing Plan

1. **Video Upload Testing**
   - Test uploading videos of different sizes and formats
   - Verify proper thumbnail generation
   - Check upload progress indicators

2. **Video Playback Testing**
   - Test streaming from server
   - Verify playback controls work correctly
   - Test full-screen mode

3. **Offline Support Testing**
   - Record videos while offline
   - Verify sync when connection is restored
   - Test viewing cached videos when offline

4. **Performance Testing**
   - Measure upload time for various video sizes
   - Check memory usage during playback
   - Verify battery consumption is reasonable

## 8. Next Steps

1. Implement video compression to optimize uploads
2. Add support for additional video formats
3. Implement advanced playback controls (speed, chapters)
4. Add video editing capabilities
5. Implement in-app screen recording
6. Add support for captions and transcription