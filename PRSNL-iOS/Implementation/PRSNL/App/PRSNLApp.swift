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
            // Show launch screen for 1.5 seconds
            try? await Task.sleep(nanoseconds: 1_500_000_000)
            
            await MainActor.run {
                self.isLaunching = false
            }
        }
    }
}

struct ContentView: View {
    var body: some View {
        TabView {
            // Dashboard Tab
            DashboardView()
                .tabItem {
                    Label("Dashboard", systemImage: "square.grid.2x2")
                }
            
            // Timeline Tab
            TimelineView()
                .tabItem {
                    Label("Timeline", systemImage: "clock")
                }
            
            // Search Tab
            SearchView()
                .tabItem {
                    Label("Search", systemImage: "magnifyingglass")
                }
            
            // Settings Tab
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
        }
        .accentColor(.red)
        .background(Color(.systemBackground))
    }
}

#Preview {
    ContentView()
}