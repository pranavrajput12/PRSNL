import SwiftUI
import UniformTypeIdentifiers
import UIKit

struct ShareView: View {
    let extensionContext: NSExtensionContext?
    @StateObject private var viewModel = ShareViewModel()
    @State private var tags: [String] = []
    @State private var tagInput = ""
    @State private var showingError = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationView {
            mainContent
        }
        .onAppear {
            viewModel.extensionContext = extensionContext
            viewModel.loadShareData()
            viewModel.loadRecentTags()
        }
        .onChange(of: viewModel.success) {
            if viewModel.success {
                // Show success animation then dismiss
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                    self.extensionContext?.completeRequest(returningItems: nil)
                }
            }
        }
        .alert("Error", isPresented: $showingError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage)
        }
        .onChange(of: viewModel.errorMessage) {
            if let error = viewModel.errorMessage {
                errorMessage = error
                showingError = true
            }
        }
    }
    
    private var mainContent: some View {
        VStack(spacing: 16) {
            // Source Preview
            if !viewModel.shareData.isEmpty {
                SharePreview(data: viewModel.shareData)
                    .padding(.horizontal)
            }
            
            // Tag Input Section
            tagInputSection
            
            // Recent Tags
            if !viewModel.recentTags.isEmpty {
                recentTagsSection
            }
            
            Spacer()
            
            // Action Buttons
            actionButtons
        }
        .navigationTitle("Save to PRSNL")
        .navigationBarTitleDisplayMode(.inline)
    }
    
    private var tagInputSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Tags")
                .font(.headline)
                .foregroundColor(.primary)
            
            HStack {
                TextField("Add tags", text: $tagInput)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .onSubmit {
                        addTag()
                    }
                
                Button("Add", action: addTag)
                    .disabled(tagInput.isEmpty)
                    .foregroundColor(.red)
            }
            
            // Tag Chips
            if !tags.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        ForEach(tags, id: \.self) { tag in
                            TagChip(tag: tag) {
                                removeTag(tag)
                            }
                        }
                    }
                }
            }
        }
        .padding(.horizontal)
    }
    
    private var recentTagsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Recent Tags")
                .font(.caption)
                .foregroundColor(.secondary)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack {
                    ForEach(viewModel.recentTags, id: \.self) { tag in
                        Button(action: {
                            if !tags.contains(tag) {
                                tags.append(tag)
                            }
                        }) {
                            Text(tag)
                                .font(.caption)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 6)
                                .background(Color.gray.opacity(0.2))
                                .foregroundColor(.primary)
                                .cornerRadius(15)
                        }
                    }
                }
            }
        }
        .padding(.horizontal)
    }
    
    private var actionButtons: some View {
        HStack {
            Button("Cancel") {
                cancel()
            }
            .foregroundColor(.red)
            
            Spacer()
            
            Button(action: capture) {
                if viewModel.isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(0.8)
                } else {
                    Text("Save to PRSNL")
                }
            }
            .disabled(viewModel.isLoading || viewModel.shareData.isEmpty)
            .buttonStyle(.borderedProminent)
            .tint(.red)
        }
        .padding()
    }
    
    private func addTag() {
        let sanitized = tagInput
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased()
        
        if !sanitized.isEmpty && !tags.contains(sanitized) {
            tags.append(sanitized)
            tagInput = ""
        }
    }
    
    private func removeTag(_ tag: String) {
        tags.removeAll { $0 == tag }
    }
    
    private func capture() {
        viewModel.capture(tags: tags)
    }
    
    private func cancel() {
        extensionContext?.completeRequest(returningItems: nil)
    }
}

// MARK: - Preview Component
struct SharePreview: View {
    let data: ShareData
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Show image if present
            if data.type == .image, let imageData = data.imageData,
               let uiImage = UIImage(data: imageData) {
                Image(uiImage: uiImage)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(maxHeight: 200)
                    .cornerRadius(8)
            }
            
            if let title = data.title {
                Text(title)
                    .font(.headline)
                    .lineLimit(2)
            }
            
            if let url = data.url {
                HStack {
                    Image(systemName: "link")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(url)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
            }
            
            if let content = data.content, !content.isEmpty {
                Text(content)
                    .font(.body)
                    .lineLimit(3)
                    .padding(.top, 4)
            }
            
            // Show capture type
            HStack {
                Image(systemName: captureTypeIcon)
                    .font(.caption)
                Text(captureTypeText)
                    .font(.caption)
            }
            .foregroundColor(.secondary)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
    
    private var captureTypeIcon: String {
        switch data.type {
        case .page:
            return "doc.text"
        case .selection:
            return "text.selection"
        case .image:
            return "photo"
        }
    }
    
    private var captureTypeText: String {
        switch data.type {
        case .page:
            return "Full Page"
        case .selection:
            return "Selection"
        case .image:
            return "Image"
        }
    }
}

// MARK: - Tag Chip Component
struct TagChip: View {
    let tag: String
    let onRemove: () -> Void
    
    var body: some View {
        HStack(spacing: 4) {
            Text(tag)
                .font(.caption)
            Button(action: onRemove) {
                Image(systemName: "xmark.circle.fill")
                    .font(.caption2)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.red.opacity(0.2))
        .foregroundColor(.red)
        .cornerRadius(15)
    }
}

// MARK: - Success Animation View
struct SuccessAnimationView: View {
    @State private var scale: CGFloat = 0.5
    @State private var opacity: Double = 0
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 60))
                .foregroundColor(.red)
                .scaleEffect(scale)
            
            Text("Saved to PRSNL")
                .font(.headline)
                .foregroundColor(.primary)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(radius: 10)
        .opacity(opacity)
        .onAppear {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                scale = 1.0
                opacity = 1.0
            }
        }
    }
}

#if DEBUG
struct ShareView_Previews: PreviewProvider {
    static var previews: some View {
        ShareView(extensionContext: nil)
    }
}
#endif