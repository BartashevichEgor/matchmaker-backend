CREATE TABLE conversation (
    id text PRIMARY KEY,
    match_id bigint NOT NULL UNIQUE,
    created_at timestamptz(3) NOT NULL DEFAULT now()
);

CREATE TABLE message (
    id bigserial PRIMARY KEY,
    conversation_id text NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    sender_user_id bigint NOT NULL,
    client_message_id varchar(128) NOT NULL,
    body varchar(4000) NOT NULL,
    created_at timestamptz(3) NOT NULL DEFAULT now(),
    CONSTRAINT uq_message_sender_client_id UNIQUE (sender_user_id, client_message_id)
);
CREATE INDEX ix_message_conversation_cursor ON message (conversation_id, created_at DESC, id DESC);

CREATE TABLE conversation_read_state (
    conversation_id text NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    user_id bigint NOT NULL,
    last_read_message_id bigint REFERENCES message(id),
    last_read_at timestamptz(3) NOT NULL DEFAULT now(),
    PRIMARY KEY (conversation_id, user_id)
);
