import SwiftUI

struct CaptureView: View {
    @StateObject private var viewModel = CaptureViewModel()
    @StateObject private var networkMonitor = NetworkMonitor.shared
    @FocusState private var focusedField: Field?
    
    enum Field {
        case url, title, content, tag
    }
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // Offline indicator
                    if !networkMonitor.isConnected {
                        HStack {
                            Image(systemName: "wifi.slash")
                            Text("Offline - Content will sync when connected")
                                .font(.caption)
                        }
                        .foregroundColor(.orange)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(Color.orange.opacity(0.1))
                        .cornerRadius(8)
                    }
                    // URL Input Section
                    VStack(alignment: .leading, spacing: 8) {
                        Label("URL", systemImage: "link")
                            .font(.headline)
                            .foregroundColor(.prsnlText)
                        
                        TextField("https://example.com", text: $viewModel.urlText)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                            .keyboardType(.URL)
                            .focused($focusedField, equals: .url)
                        
                        if !viewModel.urlText.isEmpty && !viewModel.validateURL() {
                            Text("Please enter a valid URL")
                                .font(.caption)
                                .foregroundColor(.red)
                        }
                    }
                    
                    // Title Input Section
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Title (Optional)", systemImage: "textformat")
                            .font(.headline)
                            .foregroundColor(.prsnlText)
                        
                        TextField("Give it a memorable title", text: $viewModel.titleText)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .focused($focusedField, equals: .title)
                    }
                    
                    // Content Input Section
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Content", systemImage: "doc.text")
                            .font(.headline)
                            .foregroundColor(.prsnlText)
                        
                        TextEditor(text: $viewModel.contentText)
                            .frame(minHeight: 120)
                            .padding(8)
                            .background(Color.gray.opacity(0.1))
                            .cornerRadius(8)
                            .focused($focusedField, equals: .content)
                            .onChange(of: viewModel.contentText) { oldValue, newValue in
                                // Tag suggestions disabled in minimal version
                                // TODO: Re-enable when AppState is restored
                            }
                        
                        Text("\(viewModel.contentText.count) characters")
                            .font(.caption)
                            .foregroundColor(.prsnlTextSecondary)
                    }
                    
                    // Tags Section
                    VStack(alignment: .leading, spacing: 12) {
                        Label("Tags", systemImage: "tag")
                            .font(.headline)
                            .foregroundColor(.prsnlText)
                        
                        // Tag Input
                        HStack {
                            TextField("Add tag", text: $viewModel.tagInput)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .autocapitalization(.none)
                                .focused($focusedField, equals: .tag)
                                .onSubmit {
                                    viewModel.addTag()
                                }
                            
                            Button(action: viewModel.addTag) {
                                Image(systemName: "plus.circle.fill")
                                    .foregroundColor(.red)
                            }
                            .disabled(viewModel.tagInput.isEmpty)
                        }
                        
                        // Current Tags
                        if !viewModel.tags.isEmpty {
                            FlowLayout(spacing: 8) {
                                ForEach(Array(viewModel.tags.enumerated()), id: \.offset) { index, tag in
                                    TagChip(tag: tag, onRemove: {
                                        viewModel.removeTag(at: index)
                                    })
                                }
                            }
                        }
                        
                        // Live Tag Suggestions disabled in minimal version
                        // TODO: Re-enable when AppState is restored
                        
                        // Recent Tags
                        if !viewModel.recentTags.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Recent Tags")
                                    .font(.subheadline)
                                    .foregroundColor(.prsnlTextSecondary)
                                
                                FlowLayout(spacing: 8) {
                                    ForEach(viewModel.recentTags, id: \.self) { tag in
                                        if !viewModel.tags.contains(tag) {
                                            Button {
                                                viewModel.addRecentTag(tag)
                                            } label: {
                                                Text(tag)
                                                    .font(.caption)
                                                    .padding(.horizontal, 12)
                                                    .padding(.vertical, 6)
                                                    .background(Color.gray.opacity(0.2))
                                                    .foregroundColor(.prsnlText)
                                                    .cornerRadius(15)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    // Validation Message
                    if !viewModel.isValid && !viewModel.urlText.isEmpty || !viewModel.contentText.isEmpty {
                        Text(viewModel.validationMessage)
                            .font(.caption)
                            .foregroundColor(.orange)
                            .padding(.horizontal)
                    }
                    
                    // Capture Button
                    Button(action: {
                        Task {
                            await viewModel.capture()
                        }
                    }) {
                        HStack {
                            if viewModel.isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .scaleEffect(0.8)
                            } else {
                                Image(systemName: "checkmark.circle.fill")
                            }
                            Text("Capture")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(viewModel.isValid ? Color.red : Color.gray)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    .disabled(!viewModel.isValid || viewModel.isLoading)
                    
                    Spacer(minLength: 50)
                }
                .padding()
            }
            .navigationTitle("Capture")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Clear") {
                        viewModel.clearForm()
                    }
                    .disabled(viewModel.urlText.isEmpty && viewModel.titleText.isEmpty && 
                             viewModel.contentText.isEmpty && viewModel.tags.isEmpty)
                }
            }
            .alert("Success", isPresented: $viewModel.captureSuccess) {
                Button("OK") { }
            } message: {
                Text(viewModel.successMessage)
            }
            .alert("Error", isPresented: .constant(viewModel.error != nil)) {
                Button("OK") {
                    viewModel.error = nil
                }
            } message: {
                if let error = viewModel.error {
                    Text(error.localizedDescription)
                }
            }
        }
        .preferredColorScheme(.dark)
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
                    .font(.caption)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.red.opacity(0.2))
        .foregroundColor(.red)
        .cornerRadius(15)
    }
}

// MARK: - Flow Layout
struct FlowLayout: Layout {
    var spacing: CGFloat = 8
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = FlowResult(
            in: proposal.width ?? 0,
            subviews: subviews,
            spacing: spacing
        )
        return result.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = FlowResult(
            in: bounds.width,
            subviews: subviews,
            spacing: spacing
        )
        for (offset, subview) in zip(result.offsets, subviews) {
            subview.place(at: CGPoint(x: offset.x + bounds.minX, y: offset.y + bounds.minY), proposal: proposal)
        }
    }
    
    struct FlowResult {
        var offsets: [CGPoint] = []
        var size: CGSize = .zero
        
        init(in maxWidth: CGFloat, subviews: Subviews, spacing: CGFloat) {
            var x: CGFloat = 0
            var y: CGFloat = 0
            var rowHeight: CGFloat = 0
            
            for subview in subviews {
                let size = subview.sizeThatFits(.unspecified)
                
                if x + size.width > maxWidth, x > 0 {
                    x = 0
                    y += rowHeight + spacing
                    rowHeight = 0
                }
                
                offsets.append(CGPoint(x: x, y: y))
                
                x += size.width + spacing
                rowHeight = max(rowHeight, size.height)
            }
            
            self.size = CGSize(width: maxWidth, height: y + rowHeight)
        }
    }
}

// MARK: - Preview
struct CaptureView_Previews: PreviewProvider {
    static var previews: some View {
        CaptureView()
    }
}