## 1. Domain Errors

- [ ] 1.1 Write tests for `BookError` — all cases (`notFound`, `parseFailed`, `unsupportedFormat`, `alreadyExists`, `invalidState`, `embeddingFailed`, `drmProtected`, `fetchFailed`), message propagation, pattern matching (`tests/Domain/BookErrorTests.swift`)
- [ ] 1.2 Write tests for `LLMError` — all cases (`apiKeyMissing`, `apiCallFailed`, `rateLimited`, `timeout`, `unsupportedFeature`), message propagation (`tests/Domain/LLMErrorTests.swift`)
- [ ] 1.3 Write tests for `StorageError` — all cases (`dbCorrupted`, `migrationFailed`, `writeFailed`, `notFound`), message propagation (`tests/Domain/StorageErrorTests.swift`)
- [ ] 1.4 Implement `Domain/Errors/BookError.swift` — enum conforming to `Error` with associated `String` message per case
- [ ] 1.5 Implement `Domain/Errors/LLMError.swift` — enum conforming to `Error`
- [ ] 1.6 Implement `Domain/Errors/StorageError.swift` — enum conforming to `Error`

## 2. Domain Entities

- [ ] 2.1 Write tests for `BookStatus` enum — raw values match Python (`pending`, `ingesting`, `ready`, `failed`) (`tests/Domain/BookTests.swift`)
- [ ] 2.2 Write tests for `Book` creation — valid title, empty/whitespace title throws `BookError.invalidState` (`tests/Domain/BookTests.swift`)
- [ ] 2.3 Write tests for `Book` status transitions — `startIngestion()` (pending → ingesting, invalid from ready/failed/ingesting), `completeIngestion()` (ingesting → ready, invalid from others), `failIngestion()` (ingesting → failed, invalid from others), `resetToPending()` (any → pending) (`tests/Domain/BookTests.swift`)
- [ ] 2.4 Write tests for `Book.setCurrentPage()` — valid page (>= 0), negative page throws `BookError.invalidState` (`tests/Domain/BookTests.swift`)
- [ ] 2.5 Write tests for `Book.switchEmbeddingProvider()` — sets provider + dimension, resets status to pending (`tests/Domain/BookTests.swift`)
- [ ] 2.6 Write tests for `Book` Equatable — equality by `id` only (`tests/Domain/BookTests.swift`)
- [ ] 2.7 Implement `Domain/Entities/Book.swift` — `Book` class with `BookStatus` enum, `@unchecked Sendable`, all transition methods, `Equatable` by id
- [ ] 2.8 Write tests for `Chunk` creation — valid chunk, `startPage < 1` throws, `endPage < startPage` throws (`tests/Domain/ChunkTests.swift`)
- [ ] 2.9 Write tests for `Chunk` Equatable — equality by all fields (`tests/Domain/ChunkTests.swift`)
- [ ] 2.10 Implement `Domain/Entities/Chunk.swift` — `Chunk` struct with throwing initializer, `Sendable`, `Equatable`
- [ ] 2.11 Write tests for `Conversation` creation — valid title, empty title throws `BookError.invalidState` (`tests/Domain/ConversationTests.swift`)
- [ ] 2.12 Write tests for `Conversation.rename()` — valid rename, empty title throws (`tests/Domain/ConversationTests.swift`)
- [ ] 2.13 Write tests for `Conversation` Equatable — equality by `id` only (`tests/Domain/ConversationTests.swift`)
- [ ] 2.14 Implement `Domain/Entities/Conversation.swift` — `Conversation` class with `@unchecked Sendable`, rename method, `Equatable` by id
- [ ] 2.15 Write tests for `MessageRole` enum — raw values match Python (`user`, `assistant`, `tool_result`) (`tests/Domain/ChatMessageTests.swift`)
- [ ] 2.16 Write tests for `ChatMessage` creation and Equatable (`tests/Domain/ChatMessageTests.swift`)
- [ ] 2.17 Implement `Domain/Entities/ChatMessage.swift` — `ChatMessage` struct with `MessageRole` enum, `Sendable`, `Equatable`

## 3. Domain Value Objects

- [ ] 3.1 Write tests for `PageContent` — valid creation, `pageNumber < 1` throws (`tests/Domain/PageContentTests.swift`)
- [ ] 3.2 Implement `Domain/ValueObjects/PageContent.swift` — struct with throwing initializer
- [ ] 3.3 Write tests for `ChunkData` — valid creation, empty content throws, `startPage < 1` throws, `endPage < startPage` throws, `chunkIndex < 0` throws (`tests/Domain/ChunkDataTests.swift`)
- [ ] 3.4 Implement `Domain/ValueObjects/ChunkData.swift` — struct with throwing initializer
- [ ] 3.5 Write tests for `EmbeddingVector` — valid creation, empty vector throws (`tests/Domain/EmbeddingVectorTests.swift`)
- [ ] 3.6 Implement `Domain/ValueObjects/EmbeddingVector.swift` — struct with throwing initializer
- [ ] 3.7 Implement `Domain/ValueObjects/SearchResult.swift` — struct, no validation needed (simple projection)
- [ ] 3.8 Implement `Domain/ValueObjects/BookSummary.swift` — struct, no validation needed
- [ ] 3.9 Implement `Domain/ValueObjects/PromptMessage.swift` — struct with `role`, `content`, optional `toolUseId`, optional `toolInvocations`
- [ ] 3.10 Implement `Domain/ValueObjects/ToolDefinition.swift` — struct with `name`, `description`, `parameters: [String: Any]`
- [ ] 3.11 Implement `Domain/ValueObjects/ToolInvocation.swift` — struct with `toolName`, `toolUseId`, `arguments: [String: Any]`
- [ ] 3.12 Implement `Domain/ValueObjects/ChatResponse.swift` — struct with optional `text`, `toolInvocations`, optional `usage`
- [ ] 3.13 Implement `Domain/ValueObjects/TokenUsage.swift` — struct with `inputTokens`, `outputTokens`
- [ ] 3.14 Implement `Domain/ValueObjects/ChatEvent.swift` — enum with `.toolInvocation(name:arguments:)`, `.toolResult(query:resultCount:results:)`, `.tokenUsage(inputTokens:outputTokens:)` cases

## 4. Domain Protocols

- [ ] 4.1 Implement `Domain/Protocols/BookRepository.swift` — `save(_:)`, `get(_:) -> Book?`, `getAll() -> [Book]`, `delete(_:)` (all `throws`)
- [ ] 4.2 Implement `Domain/Protocols/ChunkRepository.swift` — `saveChunks(bookId:chunks:)`, `getByBook(_:) -> [Chunk]`, `getUpToPage(bookId:page:) -> [Chunk]`, `countByBook(_:) -> Int`, `deleteByBook(_:)` (all `throws`)
- [ ] 4.3 Implement `Domain/Protocols/ConversationRepository.swift` — `save(_:)`, `get(_:) -> Conversation?`, `getByBook(_:) -> [Conversation]`, `delete(_:)` (all `throws`)
- [ ] 4.4 Implement `Domain/Protocols/ChatMessageRepository.swift` — `save(_:)`, `getByConversation(_:) -> [ChatMessage]`, `deleteByConversation(_:)` (all `throws`)
- [ ] 4.5 Implement `Domain/Protocols/EmbeddingRepository.swift` — `ensureTable(providerName:dimension:)`, `saveEmbeddings(providerName:dimension:bookId:embeddings:)`, `deleteByBook(providerName:dimension:bookId:)`, `hasEmbeddings(bookId:providerName:dimension:) -> Bool`, `search(providerName:dimension:bookId:queryVector:topK:) -> [(chunkId: String, distance: Float)]` (all `throws`)
- [ ] 4.6 Implement `Domain/Protocols/BookParser.swift` — `parse(fileAt:) async throws -> [PageContent]`
- [ ] 4.7 Implement `Domain/Protocols/TextChunker.swift` — `chunk(pages:) throws -> [ChunkData]`
- [ ] 4.8 Implement `Domain/Protocols/ChatProvider.swift` — `chat(messages:) async throws -> String`, `chatWithTools(messages:tools:) async throws -> ChatResponse`, `modelName: String`
- [ ] 4.9 Implement `Domain/Protocols/EmbeddingProvider.swift` — `embed(texts:) async throws -> [[Float]]`, `providerName: String`, `dimension: Int`
- [ ] 4.10 Implement `Domain/Protocols/RetrievalStrategy.swift` — `execute(chatProvider:messages:tools:searchFn:onEvent:) async throws -> (String, [ChatMessage])`
- [ ] 4.11 Implement `Domain/Protocols/ConversationContextStrategy.swift` — `buildContext(history:) -> [ChatMessage]`
- [ ] 4.12 Implement `Domain/Protocols/PageMappingStrategy.swift` — `mapPages(rawContent:) throws -> [PageContent]`

## 5. Verification

- [ ] 5.1 Verify all domain files have zero imports from Infra/ or third-party packages (only Foundation allowed)
- [ ] 5.2 Verify `swift build` succeeds
- [ ] 5.3 Verify `swift test` passes — all domain invariant tests green
