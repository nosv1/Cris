use serenity::model::prelude::Message;
use serenity::prelude::Context;

use crate::servers::tepcott;

pub async fn message(context: Context, msg: Message) {
    let channel_id = msg.channel_id.0.to_string();

    if channel_id == tepcott::tepcott::SUBMISSIONS_CHANNEL_ID {       // message sent in submissions channel
        let mut split_message = msg.content.split(" ");  // split message into words
        let command = split_message.next();             // get first word

        if let Some("!submit") = command {                    // if first word is !submit
            let _ = tepcott::commands::submit::
                submit(&context, &msg, split_message).await;  // handle submit command
        }
    }
}