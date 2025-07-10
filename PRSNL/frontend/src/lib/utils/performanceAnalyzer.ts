/**
 * Performance Analyzer for 3D Components
 * Helps determine server deployment impact
 */

export interface PerformanceMetrics {
  fps: number;
  memoryUsed: number;
  memoryTotal: number;
  renderTime: number;
  loadTime: number;
  fileSize: number;
  networkType: string;
  isWebGLActive: boolean;
}

export interface DeploymentRecommendation {
  status: 'EXCELLENT' | 'GOOD' | 'WARNING' | 'CRITICAL';
  recommendations: string[];
  serverImpact: 'LOW' | 'MEDIUM' | 'HIGH';
  mobileCompatible: boolean;
}

export class PerformanceAnalyzer {
  private metrics: PerformanceMetrics[] = [];
  
  addMetric(metric: PerformanceMetrics) {
    this.metrics.push(metric);
    // Keep only last 10 metrics for analysis
    if (this.metrics.length > 10) {
      this.metrics.shift();
    }
  }
  
  getAverageMetrics(): PerformanceMetrics | null {
    if (this.metrics.length === 0) return null;
    
    const avg = this.metrics.reduce((acc, metric) => ({
      fps: acc.fps + metric.fps,
      memoryUsed: acc.memoryUsed + metric.memoryUsed,
      memoryTotal: acc.memoryTotal + metric.memoryTotal,
      renderTime: acc.renderTime + metric.renderTime,
      loadTime: acc.loadTime + metric.loadTime,
      fileSize: acc.fileSize + metric.fileSize,
      networkType: metric.networkType, // Latest value
      isWebGLActive: metric.isWebGLActive
    }), { fps: 0, memoryUsed: 0, memoryTotal: 0, renderTime: 0, loadTime: 0, fileSize: 0, networkType: '', isWebGLActive: false });
    
    const count = this.metrics.length;
    return {
      fps: Math.round(avg.fps / count),
      memoryUsed: Math.round(avg.memoryUsed / count),
      memoryTotal: Math.round(avg.memoryTotal / count),
      renderTime: avg.renderTime / count,
      loadTime: avg.loadTime / count,
      fileSize: avg.fileSize / count,
      networkType: avg.networkType,
      isWebGLActive: avg.isWebGLActive
    };
  }
  
  analyzeForDeployment(): DeploymentRecommendation {
    const avgMetrics = this.getAverageMetrics();
    if (!avgMetrics) {
      return {
        status: 'WARNING',
        recommendations: ['Insufficient data for analysis'],
        serverImpact: 'MEDIUM',
        mobileCompatible: false
      };
    }
    
    const recommendations: string[] = [];
    let status: DeploymentRecommendation['status'] = 'EXCELLENT';
    let serverImpact: DeploymentRecommendation['serverImpact'] = 'LOW';
    let mobileCompatible = true;
    
    // FPS Analysis
    if (avgMetrics.fps < 30) {
      status = 'CRITICAL';
      recommendations.push('FPS too low - consider reducing 3D complexity');
      mobileCompatible = false;
    } else if (avgMetrics.fps < 50) {
      status = status === 'EXCELLENT' ? 'WARNING' : status;
      recommendations.push('FPS could be improved for better mobile experience');
    }
    
    // Memory Analysis
    const memoryPressure = (avgMetrics.memoryUsed / avgMetrics.memoryTotal) * 100;
    if (memoryPressure > 70) {
      status = 'CRITICAL';
      serverImpact = 'HIGH';
      recommendations.push('High memory pressure - optimize textures and geometries');
      mobileCompatible = false;
    } else if (memoryPressure > 50) {
      status = status === 'EXCELLENT' ? 'WARNING' : status;
      serverImpact = 'MEDIUM';
      recommendations.push('Monitor memory usage on lower-end devices');
    }
    
    if (avgMetrics.memoryUsed > 100) {
      status = status === 'EXCELLENT' ? 'WARNING' : status;
      serverImpact = 'MEDIUM';
      recommendations.push('Memory usage is high - consider LOD (Level of Detail) models');
    }
    
    // Render Time Analysis
    if (avgMetrics.renderTime > 16) {
      status = status === 'EXCELLENT' ? 'WARNING' : status;
      recommendations.push('Render time exceeds 60fps budget - optimize shaders/materials');
    }
    
    // Load Time Analysis
    if (avgMetrics.loadTime > 2000) {
      status = status === 'EXCELLENT' ? 'WARNING' : status;
      serverImpact = serverImpact === 'LOW' ? 'MEDIUM' : serverImpact;
      recommendations.push('Load time is high - consider model compression or CDN');
    }
    
    // File Size Analysis
    if (avgMetrics.fileSize > 5000) { // 5MB
      serverImpact = 'HIGH';
      recommendations.push('Large file size - compress models and use efficient formats');
    } else if (avgMetrics.fileSize > 1000) { // 1MB
      serverImpact = serverImpact === 'LOW' ? 'MEDIUM' : serverImpact;
      recommendations.push('Consider model optimization for faster loading');
    }
    
    // Network Analysis
    if (avgMetrics.networkType === '2g' || avgMetrics.networkType === 'slow-2g') {
      mobileCompatible = false;
      recommendations.push('Not suitable for slow connections - provide fallback');
    }
    
    // WebGL Analysis
    if (!avgMetrics.isWebGLActive) {
      status = 'CRITICAL';
      recommendations.push('WebGL context lost - implement recovery mechanism');
    }
    
    // Positive recommendations if performance is good
    if (recommendations.length === 0) {
      recommendations.push('Performance is excellent - ready for production deployment');
      if (avgMetrics.memoryUsed < 50 && avgMetrics.fps >= 60) {
        recommendations.push('Consider adding more visual details if desired');
      }
    }
    
    return {
      status,
      recommendations,
      serverImpact,
      mobileCompatible
    };
  }
  
  generateReport(): string {
    const avgMetrics = this.getAverageMetrics();
    const deployment = this.analyzeForDeployment();
    
    if (!avgMetrics) return 'No performance data available';
    
    return `
🔍 PERFORMANCE ANALYSIS REPORT
═══════════════════════════════

📊 AVERAGE METRICS:
   • FPS: ${avgMetrics.fps}
   • Memory: ${avgMetrics.memoryUsed}MB / ${avgMetrics.memoryTotal}MB
   • Render Time: ${avgMetrics.renderTime.toFixed(2)}ms
   • Load Time: ${avgMetrics.loadTime.toFixed(0)}ms
   • File Size: ~${avgMetrics.fileSize}KB
   • Network: ${avgMetrics.networkType}
   • WebGL: ${avgMetrics.isWebGLActive ? 'Active' : 'Lost'}

🚀 DEPLOYMENT ANALYSIS:
   • Status: ${deployment.status}
   • Server Impact: ${deployment.serverImpact}
   • Mobile Compatible: ${deployment.mobileCompatible ? 'Yes' : 'No'}

💡 RECOMMENDATIONS:
${deployment.recommendations.map(rec => `   • ${rec}`).join('\n')}

═══════════════════════════════
    `.trim();
  }
}

// Global analyzer instance
export const performanceAnalyzer = new PerformanceAnalyzer();