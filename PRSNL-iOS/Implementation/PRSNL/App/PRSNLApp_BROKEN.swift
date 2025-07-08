import SwiftUI

@main
struct PRSNLApp: App {
    @StateObject private var appState = AppState()
    
    var body: some Scene {
        WindowGroup {
            ZStack {
                if appState.isLaunching {
                    LaunchScreenView()
                        .transition(.opacity)
                } else {
                    MainTabView()
                        .environmentObject(appState)
                        .transition(.opacity)
                }
            }
            .animation(.easeInOut(duration: 0.5), value: appState.isLaunching)
            .onAppear {
                appState.initializeApp()
            }
        }
    }
}


// App State Manager
class AppState: ObservableObject {
    @Published var isLaunching = true
    @Published var isAuthenticated = false
    
    func initializeApp() {
        // Simple initialization without external dependencies
        Task {
            // Simulate minimum launch time for effect
            try? await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
            
            await MainActor.run {
                self.isAuthenticated = false // Start unauthenticated
                self.isLaunching = false
            }
        }
    }
}

struct MainTabView: View {
    var body: some View {
        TabView {
            // Timeline Tab
            SimpleTimelineView()
                .tabItem {
                    Label("Timeline", systemImage: "list.bullet")
                }
            
            // Search Tab
            SimpleSearchView()
                .tabItem {
                    Label("Search", systemImage: "magnifyingglass")
                }
            
            // Capture Tab
            SimpleCaptureView()
                .tabItem {
                    Label("Capture", systemImage: "plus.circle")
                }
            
            // Settings Tab
            SimpleSettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
        }
        .accentColor(.red)
        .preferredColorScheme(.dark)
    }
}

// Simple placeholder views to prevent crashes
struct SimpleTimelineView: View {
    var body: some View {
        NavigationView {
            VStack {
                Image(systemName: "list.bullet")
                    .font(.system(size: 50))
                    .foregroundColor(.gray)
                Text("Timeline")
                    .font(.title)
                Text("Your personal knowledge timeline will appear here")
                    .foregroundColor(.gray)
                    .multilineTextAlignment(.center)
                    .padding()
            }
            .navigationTitle("Timeline")
        }
    }
}

struct SimpleSearchView: View {
    var body: some View {
        NavigationView {
            VStack {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 50))
                    .foregroundColor(.gray)
                Text("Search")
                    .font(.title)
                Text("Search your knowledge base")
                    .foregroundColor(.gray)
                    .multilineTextAlignment(.center)
                    .padding()
            }
            .navigationTitle("Search")
        }
    }
}

struct SimpleCaptureView: View {
    var body: some View {
        NavigationView {
            VStack {
                Image(systemName: "plus.circle")
                    .font(.system(size: 50))
                    .foregroundColor(.gray)
                Text("Capture")
                    .font(.title)
                Text("Add new knowledge to your personal base")
                    .foregroundColor(.gray)
                    .multilineTextAlignment(.center)
                    .padding()
            }
            .navigationTitle("Capture")
        }
    }
}

struct SimpleSettingsView: View {
    var body: some View {
        NavigationView {
            VStack {
                Image(systemName: "gear")
                    .font(.system(size: 50))
                    .foregroundColor(.gray)
                Text("Settings")
                    .font(.title)
                Text("Configure your PRSNL app")
                    .foregroundColor(.gray)
                    .multilineTextAlignment(.center)
                    .padding()
            }
            .navigationTitle("Settings")
        }
    }
}

struct PRSNLApp_Previews: PreviewProvider {
    static var previews: some View {
        MainTabView()
    }
}