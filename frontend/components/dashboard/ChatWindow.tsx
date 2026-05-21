"use client";

import { ChatConversation } from "./types";

type ChatWindowProps = {
  selectedChat: ChatConversation;
};

const getFileIcon = (name: string) => {
  const extension = name.split(".").pop()?.toLowerCase();

  switch (extension) {
    case "pdf":
      return "PDF";

    case "doc":
    case "docx":
      return "DOC";

    case "txt":
      return "TXT";

    case "csv":
      return "CSV";

    case "md":
      return "MD";

    case "json":
      return "JSON";

    case "ppt":
    case "pptx":
      return "PPT";

    case "png":
    case "jpg":
    case "jpeg":
      return "IMG";

    default:
      return "FILE";
  }
};

export function ChatWindow({
  selectedChat,
}: ChatWindowProps) {
  return (
    <div className="flex h-full flex-col bg-slate-950/90">

      {/* SCROLLABLE CHAT AREA */}

      <div className="flex-1 overflow-y-auto px-3 py-4 sm:px-5 lg:px-8">

        <div className="mx-auto flex w-full max-w-5xl flex-col gap-5">

          {selectedChat.messages.map(
            (message, index) => {

              const isUser =
                message.from === "user";

              return (
                <div
                  key={index}
                  className={`flex w-full ${
                    isUser
                      ? "justify-end"
                      : "justify-start"
                  }`}
                >

                  {/* MESSAGE CARD */}

                  <div
                    className={`
                      relative
                      w-fit
                      max-w-[92%]
                      sm:max-w-[82%]
                      lg:max-w-[72%]
                      rounded-3xl
                      px-4
                      py-4
                      shadow-xl
                      transition-all
                      duration-200
                      ${
                        isUser
                          ? "bg-gradient-to-r from-cyan-400 to-indigo-500 text-slate-950"
                          : "border border-white/10 bg-slate-900/90 text-slate-100"
                      }
                    `}
                  >

                    {/* ATTACHMENTS */}

                    {message.attachments &&
                    message.attachments.length >
                      0 ? (

                      <div className="mb-4 flex flex-col gap-3">

                        {message.attachments.map(
                          (
                            file,
                            fileIndex
                          ) => (
                            <div
                              key={fileIndex}
                              className={`
                                flex
                                items-center
                                gap-3
                                rounded-2xl
                                border
                                p-3
                                backdrop-blur-xl
                                ${
                                  isUser
                                    ? "border-slate-900/10 bg-slate-950/10"
                                    : "border-white/10 bg-white/5"
                                }
                              `}
                            >

                              {/* FILE ICON */}

                              <div
                                className={`
                                  flex
                                  h-12
                                  w-12
                                  shrink-0
                                  items-center
                                  justify-center
                                  rounded-2xl
                                  text-xs
                                  font-bold
                                  shadow-lg
                                  ${
                                    isUser
                                      ? "bg-slate-950/20 text-slate-900"
                                      : "bg-cyan-400/10 text-cyan-300"
                                  }
                                `}
                              >
                                {getFileIcon(file)}
                              </div>

                              {/* FILE DETAILS */}

                              <div className="min-w-0 flex-1">

                                <p
                                  className={`
                                    truncate
                                    text-sm
                                    font-semibold
                                    ${
                                      isUser
                                        ? "text-slate-900"
                                        : "text-white"
                                    }
                                  `}
                                >
                                  {file}
                                </p>

                                <p
                                  className={`
                                    mt-1
                                    text-xs
                                    ${
                                      isUser
                                        ? "text-slate-800/70"
                                        : "text-slate-500"
                                    }
                                  `}
                                >
                                  Uploaded document
                                </p>
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    ) : null}

                    {/* MESSAGE CONTENT */}

                    {message.message && (
                      <p
                        className={`
                          whitespace-pre-wrap
                          break-words
                          text-sm
                          leading-7
                          sm:text-[15px]
                        `}
                      >
                        {message.message}
                      </p>
                    )}

                    {/* TIME */}

                    <div
                      className={`
                        mt-3
                        text-[11px]
                        ${
                          isUser
                            ? "text-slate-800/80"
                            : "text-slate-500"
                        }
                      `}
                    >
                      {message.time}
                    </div>
                  </div>
                </div>
              );
            }
          )}
        </div>
      </div>
    </div>
  );
}