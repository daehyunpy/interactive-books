// swift-tools-version: 6.1

import PackageDescription

let package = Package(
    name: "InteractiveBooks",
    platforms: [
        .iOS(.v26),
        .macOS(.v26),
        .visionOS(.v26),
    ],
    products: [
        .library(
            name: "InteractiveBooksCore",
            targets: ["InteractiveBooksCore"]
        ),
        .executable(
            name: "interactive-books",
            targets: ["CLI"]
        ),
    ],
    dependencies: [
        .package(
            url: "https://github.com/apple/swift-argument-parser.git",
            from: "1.5.0"
        ),
    ],
    targets: [
        .target(
            name: "InteractiveBooksCore",
            path: "Sources/InteractiveBooksCore"
        ),
        .executableTarget(
            name: "CLI",
            dependencies: [
                "InteractiveBooksCore",
                .product(name: "ArgumentParser", package: "swift-argument-parser"),
            ],
            path: "Sources/CLI"
        ),
        .testTarget(
            name: "InteractiveBooksTests",
            dependencies: ["InteractiveBooksCore"],
            path: "Tests/InteractiveBooksTests"
        ),
    ]
)
