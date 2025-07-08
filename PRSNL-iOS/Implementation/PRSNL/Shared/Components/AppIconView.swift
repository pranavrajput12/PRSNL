import SwiftUI

struct AppIconView: View {
    let size: CGFloat
    
    var body: some View {
        ZStack {
            // Background gradient
            LinearGradient(
                gradient: Gradient(colors: [Color.red, Color.red.opacity(0.8)]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            
            // Brain icon
            Image(systemName: "brain.head.profile")
                .font(.system(size: size * 0.5, weight: .light))
                .foregroundColor(.white)
                .symbolRenderingMode(.hierarchical)
        }
        .frame(width: size, height: size)
        .clipShape(RoundedRectangle(cornerRadius: size * 0.2))
    }
}

#Preview {
    VStack(spacing: 20) {
        AppIconView(size: 60)
        AppIconView(size: 120)
        AppIconView(size: 180)
    }
    .padding()
    .background(Color.black)
}