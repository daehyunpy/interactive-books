// swift-tools-version: 6.1

import PackageDescription

let package = Package(
    name: "InteractiveBooks",
    platforms: [
        .iOS(.v18),
        .macOS(.v15),
        .visionOS(.v2),
    ],
    products: [
        .library(
            name: "InteractiveBooksCore",
            targets: ["InteractiveBooksCore"],
        ),
        .executable(
            name: "interactive-books",
            targets: ["CLI"],
        ),
    ],
    dependencies: [
        .package(
            url: "https://github.com/apple/swift-argument-parser.git",
            from: "1.5.0",
        ),
    ],
    targets: [
        .systemLibrary(
            name: "CSQLite",
            path: "Sources/CSQLite",
            pkgConfig: "sqlite3",
            providers: [
                .apt(["libsqlite3-dev"]),
            ],
        ),
        .target(
            name: "InteractiveBooksCore",
            dependencies: [
                .target(name: "CSQLite", condition: .when(platforms: [.linux])),
            ],
            path: "Sources/InteractiveBooksCore",
        ),
        .executableTarget(
            name: "CLI",
            dependencies: [
                "InteractiveBooksCore",
                .product(name: "ArgumentParser", package: "swift-argument-parser"),
            ],
            path: "Sources/CLI",
        ),
        .testTarget(
            name: "InteractiveBooksTests",
            dependencies: ["InteractiveBooksCore"],
            path: "Tests/InteractiveBooksTests",
        ),
    ],
)
