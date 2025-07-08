import SwiftUI

struct SettingsView: View {
    @StateObject private var viewModel = SettingsViewModel()
    @State private var showResetConfirmation = false
    @State private var apiKeyVisible = false
    
    var body: some View {
        NavigationView {
            Form {
                // API Configuration Section
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Label("API Key", systemImage: "key.fill")
                            .font(.headline)
                            .foregroundColor(.prsnlText)
                        
                        HStack {
                            if apiKeyVisible {
                                TextField("Enter your API key", text: $viewModel.apiKey)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .autocapitalization(.none)
                                    .disableAutocorrection(true)
                            } else {
                                SecureField("Enter your API key", text: $viewModel.apiKey)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .autocapitalization(.none)
                                    .disableAutocorrection(true)
                            }
                            
                            Button(action: { apiKeyVisible.toggle() }) {
                                Image(systemName: apiKeyVisible ? "eye.slash.fill" : "eye.fill")
                                    .foregroundColor(.gray)
                            }
                        }
                        
                        if viewModel.apiKey.isEmpty {
                            Text("Required for accessing your knowledge base")
                                .font(.caption)
                                .foregroundColor(.orange)
                        }
                    }
                    .padding(.vertical, 4)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Server URL", systemImage: "server.rack")
                            .font(.headline)
                            .foregroundColor(.prsnlText)
                        
                        TextField("http://localhost:8000", text: $viewModel.serverURL)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                            .keyboardType(.URL)
                        
                        if !viewModel.validateServerURL() && !viewModel.serverURL.isEmpty {
                            Text("Please enter a valid URL")
                                .font(.caption)
                                .foregroundColor(.red)
                        }
                    }
                    .padding(.vertical, 4)
                    
                    // Test Connection Button
                    Button(action: {
                        Task {
                            await viewModel.testConnection()
                        }
                    }) {
                        HStack {
                            if viewModel.isTestingConnection {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle())
                                    .scaleEffect(0.8)
                            } else {
                                Image(systemName: "wifi")
                            }
                            Text("Test Connection")
                        }
                    }
                    .disabled(viewModel.apiKey.isEmpty || !viewModel.validateServerURL() || viewModel.isTestingConnection)
                } header: {
                    Text("API Configuration")
                } footer: {
                    Text("Configure your connection to the PRSNL backend server")
                }
                
                // Cache Management Section
                Section {
                    HStack {
                        Label("Cache Size", systemImage: "internaldrive")
                        Spacer()
                        if viewModel.isCalculatingCacheSize {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle())
                                .scaleEffect(0.8)
                        } else {
                            Text(viewModel.cacheSize)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Button(action: {
                        Task {
                            await viewModel.clearCache()
                        }
                    }) {
                        HStack {
                            if viewModel.isClearingCache {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle())
                                    .scaleEffect(0.8)
                            } else {
                                Image(systemName: "trash")
                                    .foregroundColor(.red)
                            }
                            Text("Clear Cache")
                                .foregroundColor(.red)
                        }
                    }
                    .disabled(viewModel.isClearingCache)
                    
                } header: {
                    Text("Storage")
                } footer: {
                    Text("Clearing cache will remove all temporary files and images")
                }
                
                // About Section
                Section {
                    HStack {
                        Label("Version", systemImage: "info.circle")
                        Spacer()
                        Text("\(viewModel.appVersion) (\(viewModel.buildNumber))")
                            .foregroundColor(.secondary)
                    }
                    
                    Link(destination: URL(string: "https://github.com/prsnl/ios")!) {
                        HStack {
                            Label("Source Code", systemImage: "chevron.left.forwardslash.chevron.right")
                            Spacer()
                            Image(systemName: "arrow.up.right.square")
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Link(destination: URL(string: "https://prsnl.io/privacy")!) {
                        HStack {
                            Label("Privacy Policy", systemImage: "hand.raised")
                            Spacer()
                            Image(systemName: "arrow.up.right.square")
                                .foregroundColor(.secondary)
                        }
                    }
                } header: {
                    Text("About")
                }
                
                // Reset Section
                Section {
                    Button(action: { showResetConfirmation = true }) {
                        HStack {
                            Image(systemName: "arrow.counterclockwise")
                                .foregroundColor(.orange)
                            Text("Reset to Defaults")
                                .foregroundColor(.orange)
                        }
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        viewModel.saveSettings()
                    }
                    .disabled(viewModel.apiKey.isEmpty || !viewModel.validateServerURL())
                }
            }
            .alert("Connection Test", isPresented: $viewModel.showConnectionTestResult) {
                Button("OK") { }
            } message: {
                if let result = viewModel.connectionTestResult {
                    Text("\(result.message)\n\n\(result.serverInfo)")
                }
            }
            .alert("Reset Settings", isPresented: $showResetConfirmation) {
                Button("Cancel", role: .cancel) { }
                Button("Reset", role: .destructive) {
                    viewModel.resetToDefaults()
                }
            } message: {
                Text("This will reset all settings to their default values. Your cached data will not be affected.")
            }
        }
        .preferredColorScheme(.dark)
    }
}

// MARK: - Preview
struct SettingsView_Previews: PreviewProvider {
    static var previews: some View {
        SettingsView()
    }
}