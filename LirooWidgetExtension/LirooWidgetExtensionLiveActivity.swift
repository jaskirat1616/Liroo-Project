//
//  LirooWidgetExtensionLiveActivity.swift
//  LirooWidgetExtension
//
//  Created by JASKIRAT SINGH on 2025-07-03.
//

import ActivityKit
import WidgetKit
import SwiftUI

struct LirooWidgetExtensionAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        // Dynamic stateful properties about your activity go here!
        var emoji: String
    }

    // Fixed non-changing properties about your activity go here!
    var name: String
}

struct LirooWidgetExtensionLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: LirooWidgetExtensionAttributes.self) { context in
            // Lock screen/banner UI goes here
            VStack {
                Text("Hello \(context.state.emoji)")
            }
            .activityBackgroundTint(Color.cyan)
            .activitySystemActionForegroundColor(Color.black)

        } dynamicIsland: { context in
            DynamicIsland {
                // Expanded UI goes here.  Compose the expanded UI through
                // various regions, like leading/trailing/center/bottom
                DynamicIslandExpandedRegion(.leading) {
                    Text("Leading")
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Text("Trailing")
                }
                DynamicIslandExpandedRegion(.bottom) {
                    Text("Bottom \(context.state.emoji)")
                    // more content
                }
            } compactLeading: {
                Text("L")
            } compactTrailing: {
                Text("T \(context.state.emoji)")
            } minimal: {
                Text(context.state.emoji)
            }
            .widgetURL(URL(string: "http://www.apple.com"))
            .keylineTint(Color.red)
        }
    }
}

extension LirooWidgetExtensionAttributes {
    fileprivate static var preview: LirooWidgetExtensionAttributes {
        LirooWidgetExtensionAttributes(name: "World")
    }
}

extension LirooWidgetExtensionAttributes.ContentState {
    fileprivate static var smiley: LirooWidgetExtensionAttributes.ContentState {
        LirooWidgetExtensionAttributes.ContentState(emoji: "😀")
     }
     
     fileprivate static var starEyes: LirooWidgetExtensionAttributes.ContentState {
         LirooWidgetExtensionAttributes.ContentState(emoji: "🤩")
     }
}

#Preview("Notification", as: .content, using: LirooWidgetExtensionAttributes.preview) {
   LirooWidgetExtensionLiveActivity()
} contentStates: {
    LirooWidgetExtensionAttributes.ContentState.smiley
    LirooWidgetExtensionAttributes.ContentState.starEyes
}
