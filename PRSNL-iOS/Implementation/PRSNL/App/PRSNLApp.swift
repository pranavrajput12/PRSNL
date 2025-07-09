import SwiftUI
import Foundation

@main
struct PRSNLApp: App {
    @StateObject private var appState = AppState()
    @AppStorage("isDarkMode") private var isDarkMode = false
    
    var body: some Scene {
        WindowGroup {
            if appState.isLaunching {
                LaunchScreenView()
                    .onAppear {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                            appState.isLaunching = false
                        }
                    }
            } else {
                ContentView()
                    .preferredColorScheme(isDarkMode ? .dark : .light)
                    .onAppear {
                        setupAppearance()
                    }
            }
        }
    }
    
    private func setupAppearance() {
        // Set up navigation bar appearance
        let appearance = UINavigationBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.largeTitleTextAttributes = [
            .font: UIFont.systemFont(ofSize: 34, weight: .bold)
        ]
        appearance.titleTextAttributes = [
            .font: UIFont.systemFont(ofSize: 17, weight: .semibold)
        ]
        
        UINavigationBar.appearance().standardAppearance = appearance
        UINavigationBar.appearance().scrollEdgeAppearance = appearance
        
        // Set up tab bar appearance
        let tabBarAppearance = UITabBarAppearance()
        tabBarAppearance.configureWithOpaqueBackground()
        
        UITabBar.appearance().standardAppearance = tabBarAppearance
        UITabBar.appearance().scrollEdgeAppearance = tabBarAppearance
    }
}

// Simple App State Manager
class AppState: ObservableObject {
    @Published var isLaunching = true
    
    func initializeApp() {
        // Not needed anymore - timing handled in view
    }
}

// Temporarily commenting out auth flow
// struct RootView: View {
//     @EnvironmentObject var authService: AuthService
//     @AppStorage("onboarding_completed") private var onboardingCompleted = false
//     
//     var body: some View {
//         if !authService.isAuthenticated {
//             AuthView()
//         } else if !onboardingCompleted {
//             OnboardingView()
//         } else {
//             ContentView()
//         }
//     }
// }

struct ContentView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            // Timeline Tab (Primary)
            TimelineView()
                .tabItem {
                    Label("Timeline", systemImage: "clock.fill")
                }
                .tag(0)
            
            // Videos Tab
            VideosView()
                .tabItem {
                    Label("Videos", systemImage: "play.rectangle.fill")
                }
                .tag(1)
            
            // Chat Tab
            ChatView()
                .tabItem {
                    Label("Chat", systemImage: "message.fill")
                }
                .tag(2)
            
            // Search Tab
            SearchView()
                .tabItem {
                    Label("Search", systemImage: "magnifyingglass")
                }
                .tag(3)
            
            // Settings Tab
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape.fill")
                }
                .tag(4)
        }
        .accentColor(DesignSystem.Colors.primaryRed)
        .background(Color(.systemBackground))
        .onAppear {
            // Customize tab bar appearance
            let tabBarAppearance = UITabBarAppearance()
            tabBarAppearance.configureWithOpaqueBackground()
            
            // Normal state
            tabBarAppearance.stackedLayoutAppearance.normal.iconColor = UIColor(DesignSystem.Colors.gray500)
            tabBarAppearance.stackedLayoutAppearance.normal.titleTextAttributes = [
                .font: UIFont.systemFont(ofSize: 10, weight: .medium),
                .foregroundColor: UIColor(DesignSystem.Colors.gray500)
            ]
            
            // Selected state
            tabBarAppearance.stackedLayoutAppearance.selected.iconColor = UIColor(DesignSystem.Colors.primaryRed)
            tabBarAppearance.stackedLayoutAppearance.selected.titleTextAttributes = [
                .font: UIFont.systemFont(ofSize: 10, weight: .medium),
                .foregroundColor: UIColor(DesignSystem.Colors.primaryRed)
            ]
            
            UITabBar.appearance().standardAppearance = tabBarAppearance
            UITabBar.appearance().scrollEdgeAppearance = tabBarAppearance
        }
    }
}

#Preview {
    ContentView()
}