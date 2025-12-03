import ActivityKit
import SwiftUI
import WidgetKit

// MARK: - Shared Live Activity Attributes (Duplicated for Widget Extension)
public struct ContentGenerationAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        public var progress: Double
        public var currentStep: String
        public var generationType: String
        public var totalSteps: Int
        public var currentStepNumber: Int
        
        public init(progress: Double, currentStep: String, generationType: String, totalSteps: Int, currentStepNumber: Int) {
            self.progress = progress
            self.currentStep = currentStep
            self.generationType = generationType
            self.totalSteps = totalSteps
            self.currentStepNumber = currentStepNumber
        }
    }
    
    public var generationType: String
    public var startTime: Date
    
    public init(generationType: String, startTime: Date) {
        self.generationType = generationType
        self.startTime = startTime
    }
}

// MARK: - Live Activity Widget
struct ContentGenerationLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: ContentGenerationAttributes.self) { context in
            // Lock screen/banner UI goes here
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: "sparkles")
                        .foregroundColor(.cyan)
                    Text("Generating \(context.state.generationType)...")
                        .font(.headline)
                        .foregroundColor(.primary)
                    Spacer()
                    Text("\(Int(context.state.progress * 100))%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                ProgressView(value: context.state.progress)
                    .progressViewStyle(LinearProgressViewStyle(tint: .cyan))
                    .frame(height: 4)
                
                Text(context.state.currentStep)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
            }
            .padding()
            .background(Color(.systemBackground))
            
        } dynamicIsland: { context in
            DynamicIsland {
                // Expanded UI goes here
                DynamicIslandExpandedRegion(.leading) {
                    HStack {
                        Image(systemName: "sparkles")
                            .foregroundColor(.cyan)
                        Text("Generating \(context.state.generationType)")
                            .font(.caption)
                            .foregroundColor(.primary)
                    }
                }
                
                DynamicIslandExpandedRegion(.trailing) {
                    Text("\(Int(context.state.progress * 100))%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                DynamicIslandExpandedRegion(.center) {
                    VStack(spacing: 4) {
                        ProgressView(value: context.state.progress)
                            .progressViewStyle(LinearProgressViewStyle(tint: .cyan))
                            .frame(height: 3)
                        
                        Text(context.state.currentStep)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                            .lineLimit(1)
                    }
                }
                
                DynamicIslandExpandedRegion(.bottom) {
                    HStack {
                        Text("Step \(context.state.currentStepNumber)/\(context.state.totalSteps)")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                        Spacer()
                        Text("Liroo")
                            .font(.caption2)
                            .foregroundColor(.cyan)
                    }
                }
            } compactLeading: {
                // Compact leading
                Image(systemName: "sparkles")
                    .foregroundColor(.cyan)
            } compactTrailing: {
                // Compact trailing
                Text("\(Int(context.state.progress * 100))%")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            } minimal: {
                // Minimal
                Image(systemName: "sparkles")
                    .foregroundColor(.cyan)
            }
        }
    }
}
