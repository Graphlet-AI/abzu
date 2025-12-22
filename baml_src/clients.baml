// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview

// client<llm> O3Mini {
//     provider openai
//     options {
//         model "o3-mini"
//         api_key env.OPENAI_API_KEY
//     }
// }

// client<llm> GPT4o {
//   provider openai
//   options {
//     model "gpt-4o"
//     api_key env.OPENAI_API_KEY
//   }
// }

// client<llm> Gemini25Flash {
//     provider google-ai
//     retry_policy Exponential
//     options {
//         model "gemini-2.5-flash"
//         api_key env.GEMINI_API_KEY
//         generationConfig {
//             temperature 0.0
//         }
//     }
// }

client<llm> Gemini20Flash {
    provider google-ai
    retry_policy Exponential
    options {
        model "gemini-2.0-flash"
        api_key env.GEMINI_API_KEY
        http {
            time_to_first_token_timeout_ms 60000
            idle_timeout_ms 120000
        }
        generationConfig {
            temperature 0.0
        }
    }
}

client<llm> Gemini20FlashLong {
    provider google-ai
    retry_policy Exponential
    options {
        model "gemini-2.0-flash"
        api_key env.GEMINI_API_KEY
        http {
            time_to_first_token_timeout_ms 180000
            idle_timeout_ms 180000
        }
        generationConfig {
            temperature 0.0
        }
    }
}

client<llm> Gemini25FlashLite {
    provider google-ai
    retry_policy Exponential
    options {
        model "gemini-2.5-flash-lite"
        api_key env.GEMINI_API_KEY
        http {
            time_to_first_token_timeout_ms 60000
            idle_timeout_ms 120000
        }
        generationConfig {
            temperature 0.0
        }
    }
}

// client<llm> Gemini25Pro {
//     provider google-ai
//     retry_policy Exponential
//     options {
//         model "gemini-2.5-pro"
//         api_key env.GEMINI_API_KEY
//         generationConfig {
//             temperature 0.0
//         }
//     }
// }

// client<llm> GeminiFallback {
//   provider fallback
//   retry_policy Exponential
//   options {
//     strategy [Gemini25Pro, Gemini25Flash]
//   }
// }

// // https://docs.boundaryml.com/docs/snippets/clients/fallback
// client<llm> OpenAIFallback {
//   provider fallback
//   retry_policy Constant
//   options {
//     // This will try the clients in order until one succeeds
//     strategy [O3Mini, GPT4o]
//   }
// }

// https://docs.boundaryml.com/docs/snippets/clients/retry
retry_policy Constant {
  max_retries 3
  // Strategy is optional
  strategy {
    type constant_delay
    delay_ms 200
  }
}

retry_policy Exponential {
  max_retries 3
  // Strategy is optional
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 1.5
    max_delay_ms 10000
  }
}