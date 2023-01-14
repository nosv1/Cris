
use serenity::model::gateway::Ready;
use serenity::model::prelude::Message;
use serenity::prelude::{Context, EventHandler};

use super::message;
use super::ready;

pub struct Handler;

#[serenity::async_trait]
impl EventHandler for Handler {
    async fn ready(&self, ctx: Context, ready: Ready) {
        ready::ready(ctx, ready).await;
    }
    async fn message(&self, ctx: Context, msg: Message) {
        message::message(ctx, msg).await;
    }
}