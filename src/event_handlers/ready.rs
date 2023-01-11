use serenity::model::gateway::Ready;
use serenity::model::user::OnlineStatus;
use serenity::prelude::Context;

pub struct ReadyHandler;

pub async fn ready(ctx: Context, ready: Ready) {
    println!("{} is connected!", ready.user.name);
    // ctx.set_presence(None, OnlineStatus::Invisible).await;
}