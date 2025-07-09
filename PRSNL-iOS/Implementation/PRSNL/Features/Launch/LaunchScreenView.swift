import SwiftUI

struct LaunchScreenView: View {
    @State private var logoOpacity: Double = 0
    @State private var logoScale: CGFloat = 0.5
    @State private var networkOpacity: Double = 0
    @State private var rotationAngle: Double = 0
    @State private var brainScale: CGFloat = 3.0  // Start zoomed in
    @State private var phoneFrameScale: CGFloat = 0.0  // Phone frame starts invisible
    @State private var brainPosition: CGFloat = 0  // Brain position offset
    @State private var showPhoneDetails: Bool = false
    
    var body: some View {
        ZStack {
            // Background gradient
            LinearGradient(
                colors: [
                    Color.black,
                    Color(red: 0.05, green: 0.05, blue: 0.15),
                    Color.black
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            // Simple neural network visualization
            VStack(spacing: 0) {
                // Network nodes
                HStack(spacing: 30) {
                    ForEach(0..<5) { _ in
                        Circle()
                            .fill(Color.cyan.opacity(0.8))
                            .frame(width: 12, height: 12)
                            .shadow(color: .cyan, radius: 4)
                    }
                }
                .opacity(networkOpacity)
                
                Spacer().frame(height: 40)
                
                // Cinematic "Second Brain" reveal - Brain zooms out to show it's on phone
                ZStack {
                    // Phone frame (appears during zoom out)
                    RoundedRectangle(cornerRadius: 25)
                        .stroke(
                            LinearGradient(
                                colors: [Color.white.opacity(0.8), Color.cyan.opacity(0.6)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 3
                        )
                        .frame(width: 120, height: 200)
                        .scaleEffect(phoneFrameScale)
                        .opacity(showPhoneDetails ? 1.0 : 0.0)
                    
                    // Phone screen glow background
                    RoundedRectangle(cornerRadius: 20)
                        .fill(
                            LinearGradient(
                                colors: [Color.black.opacity(0.9), Color.blue.opacity(0.1)],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                        .frame(width: 100, height: 160)
                        .scaleEffect(phoneFrameScale)
                        .opacity(showPhoneDetails ? 0.8 : 0.0)
                    
                    // The Brain (starts large, zooms out to fit in phone screen)
                    ZStack {
                        // Use brain emoji for perfect recognition
                        Text("🧠")
                            .font(.system(size: 60))
                            .shadow(color: .cyan, radius: 10)
                            .shadow(color: .blue, radius: 20)
                            .shadow(color: .white, radius: 5)
                    }
                    .scaleEffect(brainScale)
                    .offset(y: brainPosition)
                    .opacity(logoOpacity)
                    
                    // Phone details (home indicator, etc.)
                    if showPhoneDetails {
                        VStack {
                            Spacer()
                            RoundedRectangle(cornerRadius: 2)
                                .fill(Color.white.opacity(0.3))
                                .frame(width: 40, height: 4)
                                .offset(y: -10)
                        }
                        .frame(height: 200)
                        .scaleEffect(phoneFrameScale)
                    }
                }
                .rotation3DEffect(
                    .degrees(rotationAngle * 0.2),
                    axis: (x: 0, y: 1, z: 0)
                )
                
                Spacer().frame(height: 40)
                
                // App name
                Text("PRSNL")
                    .font(DesignSystem.Typography.inter(32, weight: .bold))
                    .foregroundColor(.white)
                    .opacity(logoOpacity)
                
                Spacer().frame(height: 20)
                
                // Attribution
                Text("By Pranav Rajput")
                    .font(.custom("Menlo", size: 14))
                    .fontWeight(.bold)
                    .foregroundColor(.green.opacity(0.9))
                    .tracking(1.2)
                    .opacity(logoOpacity)
            }
        }
        .onAppear {
            startAnimation()
        }
    }
    
    private func startAnimation() {
        // Phase 1: Network nodes appear
        withAnimation(.easeOut(duration: 0.8)) {
            networkOpacity = 1.0
        }
        
        // Phase 2: Brain appears large (zoomed in view)
        withAnimation(.easeOut(duration: 0.6).delay(0.3)) {
            logoOpacity = 1.0
        }
        
        // Phase 3: Cinematic zoom out - Brain scales down, phone frame scales in
        withAnimation(.easeInOut(duration: 1.5).delay(1.0)) {
            brainScale = 0.8  // Brain zooms out to phone screen size
            phoneFrameScale = 1.0  // Phone frame appears
            brainPosition = -20  // Move brain slightly up to center in phone screen
        }
        
        // Phase 4: Phone details appear
        withAnimation(.easeOut(duration: 0.8).delay(2.0)) {
            showPhoneDetails = true
        }
        
        // Phase 5: Gentle rotation throughout
        withAnimation(.linear(duration: 12).repeatForever(autoreverses: false).delay(1.5)) {
            rotationAngle = 360
        }
        
        // Phase 6: Final text appears
        withAnimation(.easeOut(duration: 0.8).delay(2.5)) {
            logoScale = 1.0
        }
    }
}

#Preview {
    LaunchScreenView()
}