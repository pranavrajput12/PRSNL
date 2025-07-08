import SwiftUI

extension Color {
    static let prsnlRed = Color(hex: "DC143C")      // Manchester United red
    static let prsnlBackground = Color(hex: "0A0A0A") // Dark background
    static let prsnlSurface = Color(hex: "1A1A1A")   // Card background
    static let prsnlText = Color(hex: "FFFFFF")      // Primary text
    static let prsnlTextSecondary = Color(hex: "A0A0A0") // Secondary text
    
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a: UInt64
        var r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            r = ((int >> 8) & 0xF) * 17
            g = ((int >> 4) & 0xF) * 17
            b = (int & 0xF) * 17
            a = 255 // Multiply by 17 to convert from 0-15 to 0-255
        case 6: // RGB (24-bit)
            a = 255
            r = int >> 16
            g = (int >> 8) & 0xFF
            b = int & 0xFF
        case 8: // ARGB (32-bit)
            a = int >> 24
            r = (int >> 16) & 0xFF
            g = (int >> 8) & 0xFF
            b = int & 0xFF
        default:
            a = 255
            r = 0
            g = 0
            b = 0
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}