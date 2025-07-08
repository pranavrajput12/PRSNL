# PRSNL iOS Video Handling Guide

## Overview
PRSNL supports video capture and playback from YouTube, Instagram, TikTok, and Twitter. All videos are processed to MP4 format for iOS compatibility.

## Video URLs Structure

### File Paths
```
Base URL: http://localhost:8000

Videos: /media/videos/{year}/{month}/{video_id}.mp4
Thumbnails: /media/thumbnails/{video_id}/{size}.jpg

Sizes: small (320x180), medium (640x360), large (1280x720)
```

### Example URLs
```swift
let videoURL = "\(baseURL)/media/videos/2025/01/abc123.mp4"
let thumbnailURL = "\(baseURL)/media/thumbnails/abc123/medium.jpg"
```

## iOS Implementation

### Video Model Extension
```swift
extension TimelineItem {
    var videoURL: URL? {
        guard itemType == "video",
              let path = filePath else { return nil }
        
        let baseURL = KeychainService.shared.get(.serverURL) ?? ""
        return URL(string: baseURL + path)
    }
    
    var thumbnailURL: URL? {
        guard let path = thumbnailUrl else { return nil }
        
        let baseURL = KeychainService.shared.get(.serverURL) ?? ""
        return URL(string: baseURL + path)
    }
    
    var formattedDuration: String? {
        guard let duration = duration else { return nil }
        
        let formatter = DateComponentsFormatter()
        formatter.allowedUnits = [.hour, .minute, .second]
        formatter.unitsStyle = .positional
        formatter.zeroFormattingBehavior = .pad
        
        return formatter.string(from: TimeInterval(duration))
    }
}
```

### Video Player View

```swift
import SwiftUI
import AVKit

struct VideoPlayerView: View {
    let item: TimelineItem
    @State private var player: AVPlayer?
    @State private var isLoading = true
    @State private var error: Error?
    
    var body: some View {
        ZStack {
            if let player = player {
                VideoPlayer(player: player)
                    .onAppear {
                        player.play()
                    }
                    .onDisappear {
                        player.pause()
                    }
            } else if isLoading {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let error = error {
                ErrorView(error: error, retry: loadVideo)
            }
        }
        .aspectRatio(16/9, contentMode: .fit)
        .background(Color.black)
        .onAppear {
            loadVideo()
        }
    }
    
    private func loadVideo() {
        guard let videoURL = item.videoURL else {
            error = VideoError.invalidURL
            isLoading = false
            return
        }
        
        isLoading = true
        error = nil
        
        let playerItem = AVPlayerItem(url: videoURL)
        player = AVPlayer(playerItem: playerItem)
        
        // Add API key to request headers if needed
        if let apiKey = KeychainService.shared.get(.apiKey) {
            let headers = ["X-API-Key": apiKey]
            let asset = AVURLAsset(url: videoURL, options: ["AVURLAssetHTTPHeaderFieldsKey": headers])
            playerItem.asset = asset
        }
        
        isLoading = false
    }
}

enum VideoError: LocalizedError {
    case invalidURL
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Unable to load video"
        }
    }
}
```

### Video Thumbnail Card

```swift
struct VideoCard: View {
    let item: TimelineItem
    @State private var thumbnailImage: UIImage?
    
    var body: some View {
        ZStack {
            // Background
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.prsnlSurface)
            
            // Thumbnail
            if let image = thumbnailImage {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(height: 200)
                    .clipped()
                    .cornerRadius(12)
            } else {
                // Loading placeholder
                Rectangle()
                    .fill(Color.gray.opacity(0.3))
                    .frame(height: 200)
                    .cornerRadius(12)
                    .overlay(
                        ProgressView()
                    )
            }
            
            // Video overlay
            VStack {
                HStack {
                    // Platform badge
                    if let platform = item.platform {
                        PlatformBadge(platform: platform)
                            .padding(8)
                    }
                    
                    Spacer()
                    
                    // Duration badge
                    if let duration = item.formattedDuration {
                        Text(duration)
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.black.opacity(0.7))
                            .foregroundColor(.white)
                            .cornerRadius(4)
                            .padding(8)
                    }
                }
                
                Spacer()
                
                // Play button overlay
                Image(systemName: "play.circle.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.white)
                    .shadow(radius: 4)
            }
        }
        .frame(height: 200)
        .onAppear {
            loadThumbnail()
        }
    }
    
    private func loadThumbnail() {
        guard let url = item.thumbnailURL else { return }
        
        Task {
            do {
                let (data, _) = try await URLSession.shared.data(from: url)
                if let image = UIImage(data: data) {
                    await MainActor.run {
                        self.thumbnailImage = image
                    }
                }
            } catch {
                print("Failed to load thumbnail: \(error)")
            }
        }
    }
}

struct PlatformBadge: View {
    let platform: String
    
    var icon: String {
        switch platform.lowercased() {
        case "youtube":
            return "play.rectangle.fill"
        case "instagram", "instagram_reel", "instagram_post":
            return "camera.fill"
        case "tiktok":
            return "music.note"
        case "twitter":
            return "bird.fill"
        default:
            return "video.fill"
        }
    }
    
    var color: Color {
        switch platform.lowercased() {
        case "youtube":
            return .red
        case "instagram", "instagram_reel", "instagram_post":
            return .purple
        case "tiktok":
            return .black
        case "twitter":
            return .blue
        default:
            return .gray
        }
    }
    
    var body: some View {
        Image(systemName: icon)
            .font(.caption)
            .foregroundColor(.white)
            .padding(6)
            .background(color)
            .cornerRadius(6)
    }
}
```

### Video API Integration

```swift
extension APIClient {
    // Stream video
    func streamVideo(id: String) -> URL? {
        guard let baseURL = URL(string: self.baseURL) else { return nil }
        return baseURL.appendingPathComponent("videos/\(id)/stream")
    }
    
    // Get video metadata
    func fetchVideoMetadata(id: String) async throws -> VideoMetadata {
        return try await request("videos/\(id)/metadata", method: "GET")
    }
    
    // Request video transcode
    func requestTranscode(id: String, quality: VideoQuality) async throws {
        let body = ["target_quality": quality.rawValue]
        let _: EmptyResponse = try await request(
            "videos/\(id)/transcode",
            method: "POST",
            body: body
        )
    }
}

struct VideoMetadata: Codable {
    let id: String
    let url: String
    let title: String
    let description: String?
    let author: String?
    let duration: Int
    let videoPath: String
    let thumbnailPath: String
    let platform: String
    let metadata: [String: Any]?
    let downloadedAt: Date
    let status: String
    
    enum CodingKeys: String, CodingKey {
        case id, url, title, description, author, duration, platform, metadata, status
        case videoPath = "video_path"
        case thumbnailPath = "thumbnail_path"
        case downloadedAt = "downloaded_at"
    }
}
```

### Efficient Video List

```swift
struct VideoTimelineView: View {
    @State private var videos: [TimelineItem] = []
    
    var body: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                ForEach(videos) { item in
                    NavigationLink(destination: VideoDetailView(item: item)) {
                        VideoCard(item: item)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding()
        }
    }
}
```

### Video Caching Strategy

```swift
class VideoCache {
    static let shared = VideoCache()
    private let cache = URLCache(
        memoryCapacity: 100 * 1024 * 1024, // 100 MB
        diskCapacity: 1 * 1024 * 1024 * 1024 // 1 GB
    )
    
    func configureCaching() {
        URLCache.shared = cache
        
        // Configure URLSession for video requests
        let config = URLSessionConfiguration.default
        config.urlCache = cache
        config.requestCachePolicy = .returnCacheDataElseLoad
    }
    
    func preloadThumbnails(for items: [TimelineItem]) {
        for item in items {
            guard let url = item.thumbnailURL else { continue }
            
            Task {
                let request = URLRequest(url: url)
                if cache.cachedResponse(for: request) == nil {
                    try? await URLSession.shared.data(from: url)
                }
            }
        }
    }
}
```

## Best Practices

1. **Thumbnail First**: Always show thumbnail before loading video
2. **Progressive Loading**: Use AVPlayer's streaming capabilities
3. **Memory Management**: Pause/release players when off-screen
4. **Error Handling**: Show clear messages for network/format issues
5. **Network Awareness**: Check connection before video playback
6. **Caching**: Cache thumbnails aggressively, videos sparingly

## Platform-Specific Considerations

### Instagram
- May require authentication cookies
- Different types: regular posts, reels
- Check `platform` field for specific type

### YouTube
- Typically highest quality videos
- May have age restrictions
- Support for various resolutions

### TikTok
- Usually shorter videos
- Vertical orientation common
- Lower file sizes

### Twitter
- Variable quality
- May be embedded in threads
- Often shorter clips

## Performance Tips

1. **Lazy Loading**: Only load videos when visible
2. **Thumbnail Sizes**: Use appropriate size for context
3. **Preloading**: Preload next video in timeline
4. **Quality Selection**: Let users choose video quality
5. **Download Option**: Allow offline viewing for Pro users

This guide provides everything needed to implement robust video support in the iOS app.