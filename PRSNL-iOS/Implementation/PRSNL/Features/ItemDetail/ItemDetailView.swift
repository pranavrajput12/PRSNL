import SwiftUI

struct ItemDetailView: View {
    var item: Item? = nil
    var itemId: String? = nil
    
    @State private var loadedItem: Item?
    @State private var isLoading = false
    @State private var error: String?
    
    init(item: Item) {
        self.item = item
    }
    
    init(itemId: String) {
        self.itemId = itemId
    }
    
    var body: some View {
        ZStack {
            Color.prsnlBackground.ignoresSafeArea()
            
            if isLoading {
                ProgressView()
            } else if let error = error {
                VStack {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 64))
                        .foregroundColor(.prsnlRed)
                        .padding()
                    
                    Text("Error loading item")
                        .font(.title2)
                        .foregroundColor(.prsnlText)
                        .padding(.bottom)
                    
                    Text(error)
                        .foregroundColor(.prsnlTextSecondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
            } else if let displayItem = item ?? loadedItem {
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        // Title
                        Text(displayItem.title)
                            .font(.title)
                            .foregroundColor(.prsnlText)
                            .padding(.bottom, 8)
                        
                        // Type and Status
                        HStack {
                            Text(displayItem.itemType.rawValue.capitalized)
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background(itemTypeColor(for: displayItem.itemType))
                                .foregroundColor(.white)
                                .cornerRadius(4)
                            
                            if displayItem.status == .archived {
                                Text("Archived")
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 3)
                                    .background(Color.gray)
                                    .foregroundColor(.white)
                                    .cornerRadius(4)
                            }
                            
                            Spacer()
                            
                            Text("Viewed \(displayItem.accessCount) times")
                                .font(.caption)
                                .foregroundColor(.prsnlTextSecondary)
                        }
                        
                        // URL if available
                        if let url = displayItem.url, !url.isEmpty {
                            Link(destination: URL(string: url) ?? URL(string: "https://example.com")!) {
                                HStack {
                                    Image(systemName: "link")
                                    Text(url)
                                        .lineLimit(1)
                                }
                                .font(.caption)
                                .foregroundColor(.blue)
                            }
                            .padding(.vertical, 4)
                        }
                        
                        // Content
                        Text(displayItem.content)
                            .foregroundColor(.prsnlText)
                        
                        // Summary if available
                        if let summary = displayItem.summary, !summary.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Summary")
                                    .font(.headline)
                                    .foregroundColor(.prsnlText)
                                    .padding(.top, 8)
                                
                                Text(summary)
                                    .foregroundColor(.prsnlTextSecondary)
                                    .padding()
                                    .background(Color.gray.opacity(0.1))
                                    .cornerRadius(8)
                            }
                        }
                        
                        // Tags
                        if !displayItem.tags.isEmpty {
                            Text("Tags")
                                .font(.headline)
                                .foregroundColor(.prsnlText)
                                .padding(.top, 8)
                            
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack {
                                    ForEach(displayItem.tags, id: \.self) { tag in
                                        Text(tag)
                                            .font(.caption)
                                            .foregroundColor(.white)
                                            .padding(.vertical, 4)
                                            .padding(.horizontal, 8)
                                            .background(Color.prsnlRed)
                                            .cornerRadius(8)
                                    }
                                }
                            }
                        }
                        
                        // Attachment gallery
                        if let attachments = displayItem.attachments, !attachments.isEmpty {
                            Text("Attachments")
                                .font(.headline)
                                .foregroundColor(.prsnlText)
                                .padding(.top)
                            
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 12) {
                                    ForEach(attachments, id: \.id) { attachment in
                                        if attachment.fileType == "image" {
                                            AsyncImage(url: URL(string: APIClient.shared.serverURL + attachment.filePath)) { image in
                                                image
                                                    .resizable()
                                                    .aspectRatio(contentMode: .fill)
                                                    .frame(width: 200, height: 150)
                                                    .clipped()
                                                    .cornerRadius(8)
                                            } placeholder: {
                                                RoundedRectangle(cornerRadius: 8)
                                                    .fill(Color.gray.opacity(0.2))
                                                    .frame(width: 200, height: 150)
                                                    .overlay(ProgressView())
                                            }
                                        } else {
                                            // Display non-image attachments
                                            VStack {
                                                Image(systemName: attachmentTypeIcon(for: attachment))
                                                    .font(.system(size: 32))
                                                    .foregroundColor(.prsnlTextSecondary)
                                                    .frame(width: 200, height: 120)
                                                    .background(Color.gray.opacity(0.1))
                                                    .cornerRadius(8)
                                                
                                                Text(attachment.mimeType.components(separatedBy: "/").last ?? "file")
                                                    .font(.caption)
                                                    .foregroundColor(.prsnlTextSecondary)
                                            }
                                            .frame(width: 200, height: 150)
                                        }
                                    }
                                }
                                .padding(.horizontal)
                            }
                        }
                        
                        // Dates
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Created: \(formattedDate(displayItem.createdAt))")
                                .font(.caption)
                                .foregroundColor(.prsnlTextSecondary)
                            
                            Text("Updated: \(formattedDate(displayItem.updatedAt))")
                                .font(.caption)
                                .foregroundColor(.prsnlTextSecondary)
                            
                            if let accessedAt = displayItem.accessedAt {
                                Text("Last accessed: \(formattedDate(accessedAt))")
                                    .font(.caption)
                                    .foregroundColor(.prsnlTextSecondary)
                            }
                        }
                        .padding(.top, 16)
                    }
                    .padding()
                }
            }
        }
        .navigationTitle("Item Details")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            if item == nil, let id = itemId {
                await loadItem(id: id)
            }
        }
    }
    
    private func loadItem(id: String) async {
        isLoading = true
        error = nil
        
        do {
            loadedItem = try await APIClient.shared.fetchItem(id: id)
            isLoading = false
        } catch let apiError as APIError {
            isLoading = false
            self.error = apiError.localizedDescription
        } catch let err {
            isLoading = false
            self.error = err.localizedDescription
        }
    }
    
    // Helper to determine icon for attachment type
    private func attachmentTypeIcon(for attachment: Attachment) -> String {
        let type = attachment.fileType.lowercased()
        let mime = attachment.mimeType.lowercased()
        
        if type.contains("image") || mime.contains("image") {
            return "photo"
        } else if type.contains("video") || mime.contains("video") {
            return "video"
        } else if type.contains("audio") || mime.contains("audio") {
            return "music.note"
        } else if mime.contains("pdf") {
            return "doc.text"
        } else if mime.contains("doc") || mime.contains("word") {
            return "doc"
        } else if mime.contains("excel") || mime.contains("sheet") {
            return "chart.bar"
        } else {
            return "paperclip"
        }
    }
    
    // Helper to determine item type color
    private func itemTypeColor(for type: ItemType) -> Color {
        switch type {
        case .note:
            return Color.blue
        case .article:
            return Color.green
        case .video:
            return Color.red
        case .audio:
            return Color.purple
        case .image:
            return Color.orange
        case .document:
            return Color.cyan
        case .other:
            return Color.gray
        }
    }
    
    // Helper for date formatting
    private func formattedDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct ItemDetailView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            ItemDetailView(itemId: "1")
        }
    }
}