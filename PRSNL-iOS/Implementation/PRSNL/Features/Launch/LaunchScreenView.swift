import SwiftUI

struct LaunchScreenView: View {
    var body: some View {
        VStack {
            Spacer()
            
            Text("PRSNL")
                .font(.largeTitle)
                .fontWeight(.bold)
                .foregroundColor(.primary)
            
            Text("Your Personal Knowledge Base")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .padding(.top, 8)
            
            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(UIColor.systemBackground))
    }
}

#Preview {
    LaunchScreenView()
}