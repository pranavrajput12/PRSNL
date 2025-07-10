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
    @State private var isAuthenticated = false
    
    var body: some View {
        Group {
            if isAuthenticated {
                MainTabView(selectedTab: $selectedTab)
            } else {
                SimpleLoginView()
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: NSNotification.Name("userDidLogin"))) { _ in
            checkAuthentication()
        }
        .onReceive(NotificationCenter.default.publisher(for: NSNotification.Name("userDidLogout"))) { _ in
            checkAuthentication()
        }
        .onAppear {
            checkAuthentication()
        }
    }
    
    private func checkAuthentication() {
        isAuthenticated = APIConfiguration.shared.isAuthenticated
        print("🔐 Authentication state: \(isAuthenticated ? "Authenticated" : "Not authenticated")")
    }
}

struct MainTabView: View {
    @Binding var selectedTab: Int
    
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

struct SimpleLoginView: View {
    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                Spacer()
                
                VStack(spacing: 8) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 60))
                        .foregroundColor(.blue)
                    
                    Text("PRSNL")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    Text("Your Personal Knowledge Base")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding(.bottom, 40)
                
                VStack(spacing: 16) {
                    TextField("Email", text: $email)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .autocapitalization(.none)
                        .keyboardType(.emailAddress)
                    
                    SecureField("Password", text: $password)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                    
                    Button(action: {
                        Task {
                            await login()
                        }
                    }) {
                        HStack {
                            if isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .scaleEffect(0.8)
                            }
                            Text("Sign In")
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                    .disabled(isLoading || email.isEmpty || password.isEmpty)
                    
                    Button(action: {
                        Task {
                            await register()
                        }
                    }) {
                        HStack {
                            if isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .scaleEffect(0.8)
                            }
                            Text("Create Account")
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                    .disabled(isLoading || email.isEmpty || password.isEmpty)
                }
                .padding(.horizontal, 32)
                
                if let errorMessage = errorMessage {
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .padding(.horizontal, 32)
                        .multilineTextAlignment(.center)
                }
                
                Spacer()
            }
            .navigationTitle("")
            .navigationBarHidden(true)
        }
    }
    
    private func login() async {
        guard !email.isEmpty, !password.isEmpty else {
            errorMessage = "Please fill in all fields"
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        do {
            let response = try await APIClient.shared.login(email: email, password: password)
            print("🔐 Login successful for user: \(response.user.email)")
            
            isLoading = false
            NotificationCenter.default.post(name: NSNotification.Name("userDidLogin"), object: nil)
        } catch {
            isLoading = false
            errorMessage = "Login failed. Please try again."
            print("❌ Login error: \(error)")
        }
    }
    
    private func register() async {
        guard !email.isEmpty, !password.isEmpty else {
            errorMessage = "Please fill in all fields"
            return
        }
        
        guard password.count >= 6 else {
            errorMessage = "Password must be at least 6 characters"
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        do {
            let response = try await APIClient.shared.register(email: email, password: password, name: "User")
            print("🔐 Registration successful for user: \(response.user.email)")
            
            isLoading = false
            NotificationCenter.default.post(name: NSNotification.Name("userDidLogin"), object: nil)
        } catch {
            isLoading = false
            errorMessage = "Registration failed. Please try again."
            print("❌ Registration error: \(error)")
        }
    }
}

#Preview {
    ContentView()
}