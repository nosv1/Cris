use serenity::model::prelude::Message;
use serenity::prelude::Context;

use crate::servers::tepcott;

pub async fn message(context: Context, message: Message) {
    let channel_id = message.channel_id.0.to_string();
    let guild = match message.guild(&context) {
        Some(guild) => guild,
        None => return,
    };
    let author = &message.author;

    if channel_id == tepcott::tepcott::SUBMISSIONS_CHANNEL_ID {       // message sent in submissions channel
        let mut split_message = message.content.split(" ");  // split message into words
        let command = split_message.next();             // get first word

        match command {
            Some("!submit") => {                    // if first word is !submit
                let _ = tepcott::commands::submit::
                    submit(&context, &message, split_message).await;  // handle submit command
            }
            _ => {}
        }
    } else if channel_id == tepcott::tepcott::IGNORE_2_CHANNEL_ID {
        let mut split_message = message.content.split(" ");  // split message into words
        let command = split_message.next();             // get first word
    
        match command {
            Some("..t") => {
            },
            _ => {}
        }
    } else {
        let mut split_message = message.content.split(" ");  // split message into words
        let command = split_message.next();             // get first word

        match command {
            Some("!updatedivs") => { 
                if !author.has_role(
                    &context.http, 
                    guild.id, 
                    tepcott::tepcott::DOUBLE_D_ROLE_ID).await.unwrap() 
                { return; }                                                   // not double d
                
                let _ = message.channel_id.broadcast_typing(&context).await;
                let _ = tepcott::commands::update_divs::
                    update_division_roles(&context, &message, &guild).await;  // handle update divs command
            },
            _ => {}
        }
    }
}