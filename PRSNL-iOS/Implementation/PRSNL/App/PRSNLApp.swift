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
                    ContentView()
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

// Simple App State Manager
class AppState: ObservableObject {
    @Published var isLaunching = true
    
    func initializeApp() {
        Task {
            // Show beautiful launch screen for 2 seconds
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            
            await MainActor.run {
                self.isLaunching = false
            }
        }
    }
}

struct ContentView: View {
    var body: some View {
        TabView {
            // Timeline Tab
            NavigationView {
                VStack(spacing: 20) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 60))
                        .foregroundColor(.red)
                    
                    Text("PRSNL")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    Text("Personal Knowledge Base")
                        .font(.subheadline)
                        .foregroundColor(.gray)
                    
                    Text("✅ App is working!")
                        .font(.title2)
                        .foregroundColor(.green)
                        .padding()
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(10)
                    
                    Text("The app has successfully launched and is running without crashes.")
                        .multilineTextAlignment(.center)
                        .padding()
                        .foregroundColor(.secondary)
                }
                .navigationTitle("Timeline")
            }
            .tabItem {
                Label("Timeline", systemImage: "list.bullet")
            }
            
            // Search Tab
            NavigationView {
                VStack {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 50))
                        .foregroundColor(.blue)
                    Text("Search")
                        .font(.title)
                    Text("Search functionality will be implemented here")
                        .foregroundColor(.gray)
                        .multilineTextAlignment(.center)
                        .padding()
                }
                .navigationTitle("Search")
            }
            .tabItem {
                Label("Search", systemImage: "magnifyingglass")
            }
            
            // Settings Tab
            NavigationView {
                VStack {
                    Image(systemName: "gear")
                        .font(.system(size: 50))
                        .foregroundColor(.gray)
                    Text("Settings")
                        .font(.title)
                    Text("App settings will be configured here")
                        .foregroundColor(.gray)
                        .multilineTextAlignment(.center)
                        .padding()
                }
                .navigationTitle("Settings")
            }
            .tabItem {
                Label("Settings", systemImage: "gear")
            }
        }
        .accentColor(.red)
        .background(Color(.systemBackground))
        .preferredColorScheme(.light)
    }
}

#Preview {
    ContentView()
}