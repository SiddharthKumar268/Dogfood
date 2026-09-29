# Data Model

## Collections

### `users`
- **Fields:** `_id` (ObjectId), `email` (String), `password` (String), `role` (Enum: organizer, judge, participant)
- **Indexes:** Unique index on `email`

### `events`
- **Fields:** `_id` (ObjectId), `name` (String), `startDate` (Date), `endDate` (Date), `prizes` (Array of Strings)

### `teams`
- **Fields:** `_id` (ObjectId), `name` (String), `inviteCode` (String), `members` (Array of references to users)

### `submissions`
- **Fields:** `_id` (ObjectId), `title` (String), `description` (String), `track` (String), `status` (Enum), `eventId` (Ref), `teamId` (Ref)

### `rubrics`
- **Fields:** `_id` (ObjectId), `criteria` (Array of objects: `{name: String, weight: Number}`)
- **Constraints:** Weights must sum to 1.0

### `judgeAssignments`
- **Fields:** `_id` (ObjectId), `judgeId` (Ref), `submissionId` (Ref), `status` (String)
- **Indexes:** Compound index on `(judgeId, submissionId)`

### `scores`
- **Fields:** `_id` (ObjectId), `assignmentId` (Ref), `rawTotal` (Number), `normalizedTotal` (Number)

### `sessions`
- **Fields:** `_id` (ObjectId), `token` (String), `userId` (Ref)
- **Indexes:** Unique index on `token`

## Additional Details
- **CSV Export Field Mapping:** Rank, Title, Track, RawAvg, NormalizedAvg, JudgeCount
- **References:** String references or ObjectIds are used consistently.
- **Edge cases:** Handles duplicate scores or missing judge reviews efficiently.
