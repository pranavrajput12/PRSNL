import SwiftUI

struct LaunchScreenView: View {
    @State private var isAnimating = false
    
    var body: some View {
        VStack(spacing: DesignSystem.Spacing.space4) {
            Spacer()
            
            // Logo or Icon placeholder
            ZStack {
                Circle()
                    .fill(DesignSystem.Colors.primaryRed)
                    .frame(width: 100, height: 100)
                    .scaleEffect(isAnimating ? 1.0 : 0.9)
                    .opacity(isAnimating ? 1.0 : 0.8)
                
                Text("P")
                    .font(DesignSystem.Typography.inter(48, weight: .bold))
                    .foregroundColor(.white)
            }
            .animation(
                Animation.easeInOut(duration: 1.0)
                    .repeatForever(autoreverses: true),
                value: isAnimating
            )
            
            Text("PRSNL")
                .font(DesignSystem.Typography.inter(DesignSystem.Typography.text4XL, weight: .bold))
                .foregroundColor(DesignSystem.Colors.primaryRed)
            
            Text("Your Personal Knowledge Base")
                .font(DesignSystem.Typography.inter(DesignSystem.Typography.textLG))
                .foregroundColor(DesignSystem.Colors.gray600)
                .padding(.top, DesignSystem.Spacing.space2)
            
            Spacer()
            
            // Loading indicator
            ProgressView()
                .progressViewStyle(CircularProgressViewStyle(tint: DesignSystem.Colors.primaryRed))
                .scaleEffect(1.2)
                .padding(.bottom, DesignSystem.Spacing.space12)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(UIColor.systemBackground))
        .onAppear {
            isAnimating = true
        }
    }
}

#Preview {
    LaunchScreenView()
}