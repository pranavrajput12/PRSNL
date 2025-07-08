import Foundation
import Network
import Combine

/// Monitors network connectivity and publishes status changes
class NetworkMonitor: ObservableObject {
    /// Shared instance for app-wide network monitoring
    static let shared = NetworkMonitor()
    
    /// The network path monitor
    private let monitor = NWPathMonitor()
    
    /// Published property that indicates network connectivity status
    @Published var isConnected: Bool = false
    
    /// Queue for network monitoring
    private let queue = DispatchQueue(label: "NetworkMonitorQueue")
    
    private init() {
        startMonitoring()
    }
    
    /// Starts monitoring network connectivity
    private func startMonitoring() {
        monitor.pathUpdateHandler = { [weak self] path in
            // Update on main thread since this drives UI changes
            DispatchQueue.main.async {
                self?.isConnected = path.status == .satisfied
            }
        }
        
        // Start monitoring on background queue
        monitor.start(queue: queue)
    }
    
    /// Stops network monitoring
    func stopMonitoring() {
        monitor.cancel()
    }
}