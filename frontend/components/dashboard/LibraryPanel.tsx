import { useState, useEffect } from "react";

type UploadedFile = {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  processing_status: string;
  uploaded_at: string;
};

type Summary = {
  id: string;
  file_id: string;
  title: string;
  granularity: string;
  summary_data: {
    title: string;
    overall_summary: string;
    key_topics: {
      name: string;
      summary: string;
      core_concepts?: { name: string; definition: string; explanation: string }[];
      formulas?: { equation: string; description: string }[];
      citations?: string[];
    }[];
  };
  created_at: string;
};

type QuizQuestion = {
  id: string;
  question_text: string;
  question_type: string;
  options: string[];
  correct_answer_idx: number;
  difficulty: string;
  explanation: string;
  source_citation?: string;
};

type Quiz = {
  id: string;
  title: string;
  file_id: string;
  created_at: string;
  questions: QuizQuestion[];
};

export function LibraryPanel() {
  const [activeTab, setActiveTab] = useState<"files" | "quizzes">("files");
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Active resource loaders
  const [selectedSummary, setSelectedSummary] = useState<Summary | null>(null);
  const [selectedQuiz, setSelectedQuiz] = useState<Quiz | null>(null);
  const [selectedSyllabus, setSelectedSyllabus] = useState<any | null>(null);
  const [syllabi, setSyllabi] = useState<Record<string, any>>({});

  // Quiz state manager
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  const [selectedOptionIdx, setSelectedOptionIdx] = useState<number | null>(null);
  const [isAnswerChecked, setIsAnswerChecked] = useState(false);
  const [quizScore, setQuizScore] = useState(0);
  const [isQuizComplete, setIsQuizComplete] = useState(false);

  // Load user uploaded files
  const fetchFiles = async () => {
    setIsLoading(true);
    try {
      const resp = await fetch("http://127.0.0.1:8000/upload/files?user_id=1");
      if (resp.ok) {
        const data = await resp.json();
        setFiles(data.files || []);
      }
    } catch (err) {
      console.error("Failed to load library files:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Load all generated summaries for active user (fetches dynamically from user's files)
  const fetchSummariesAndQuizzes = async (filesList: UploadedFile[]) => {
    const loadedSummaries: Summary[] = [];
    const loadedQuizzes: Quiz[] = [];

    for (const file of filesList) {
      try {
        // Fetch summary
        const sumResp = await fetch(`http://127.0.0.1:8000/summary/file/${file.id}`);
        if (sumResp.ok) {
          const sumData = await sumResp.json();
          loadedSummaries.push(sumData);
        }
      } catch (err) {
        // Suppress expected 404s for unsummarized files
      }

      try {
        // Fetch quizzes
        const quizResp = await fetch(`http://127.0.0.1:8000/quiz/file/${file.id}`);
        if (quizResp.ok) {
          const quizData = await quizResp.json();
          if (Array.isArray(quizData)) {
            loadedQuizzes.push(...quizData);
          } else if (quizData && quizData.id) {
            loadedQuizzes.push(quizData);
          }
        }
      } catch (err) {
        // Suppress expected 404s
      }
    }

    setSummaries(loadedSummaries);
    setQuizzes(loadedQuizzes);
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchSyllabusForFiles = async (filesList: UploadedFile[]) => {
    const mappedSyllabi: Record<string, any> = {};
    for (const file of filesList) {
      try {
        const resp = await fetch(`http://127.0.0.1:8000/syllabus/file/${file.id}`);
        if (resp.ok) {
          const data = await resp.json();
          if (data.syllabus_detected) {
            mappedSyllabi[file.id] = data;
          }
        }
      } catch (err) {
        // Suppress expected 404s
      }
    }
    setSyllabi(mappedSyllabi);
  };

  useEffect(() => {
    if (files.length > 0) {
      fetchSummariesAndQuizzes(files);
      fetchSyllabusForFiles(files);
    }
  }, [files]);

  // Quiz helper functions
  const handleSelectOption = (idx: number) => {
    if (isAnswerChecked) return;
    setSelectedOptionIdx(idx);
  };

  const handleCheckAnswer = () => {
    if (selectedOptionIdx === null || !selectedQuiz) return;
    
    const currentQuestion = selectedQuiz.questions[currentQuestionIdx];
    if (selectedOptionIdx === currentQuestion.correct_answer_idx) {
      setQuizScore((prev) => prev + 1);
    }
    setIsAnswerChecked(true);
  };

  const handleNextQuestion = () => {
    if (!selectedQuiz) return;
    setSelectedOptionIdx(null);
    setIsAnswerChecked(false);

    if (currentQuestionIdx + 1 < selectedQuiz.questions.length) {
      setCurrentQuestionIdx((prev) => prev + 1);
    } else {
      setIsQuizComplete(true);
    }
  };

  const handleRestartQuiz = () => {
    setCurrentQuestionIdx(0);
    setSelectedOptionIdx(null);
    setIsAnswerChecked(false);
    setQuizScore(0);
    setIsQuizComplete(false);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div className="mx-auto max-w-6xl rounded-lg border border-slate-800 bg-slate-950 p-4 sm:p-6 shadow-2xl shadow-black/40">
      
      {/* HEADER SECTION */}
      <div className="mb-6 flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 sm:flex-row sm:items-center">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-slate-400">
            Resource Library
          </p>
          <h2 className="mt-1 text-2xl font-bold text-white sm:text-3xl">
            Study Library
          </h2>
          <p className="text-xs text-slate-400">
            View your generated revision notes, flashcards, and quizzes.
          </p>
        </div>

        {/* RESOURCE TOGGLE BAR */}
        <div className="flex items-center gap-1 rounded-md border border-slate-800 bg-slate-900 p-1">
          <button
            onClick={() => {
              setActiveTab("files");
              setSelectedSummary(null);
              setSelectedQuiz(null);
            }}
            className={`rounded px-4 py-2 text-xs font-semibold transition-all duration-200 ${
              activeTab === "files" && !selectedSummary && !selectedQuiz
                ? "bg-blue-600 text-white"
                : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            Documents
          </button>
          <button
            onClick={() => {
              setActiveTab("quizzes");
              setSelectedSummary(null);
              setSelectedQuiz(null);
            }}
            className={`rounded px-4 py-2 text-xs font-semibold transition-all duration-200 ${
              activeTab === "quizzes" || selectedQuiz
                ? "bg-blue-600 text-white"
                : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            Quizzes ({quizzes.length})
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
          <p className="text-sm font-medium animate-pulse">Loading library resources...</p>
        </div>
      )}

      {/* RENDER VIEW: DETAILED SUMMARY VIEWER */}
      {selectedSummary && (
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-6 animate-fade-in">
          <button
            onClick={() => setSelectedSummary(null)}
            className="mb-4 text-xs font-semibold text-blue-400 hover:underline"
          >
            ← Back to Library
          </button>
          <h3 className="text-2xl font-bold text-white">{selectedSummary.summary_data.title}</h3>
          <p className="mt-4 text-slate-300 leading-relaxed bg-slate-950 p-4 rounded-md border border-slate-800/60">
            {selectedSummary.summary_data.overall_summary}
          </p>

          <div className="mt-8 space-y-6">
            <h4 className="text-lg font-bold text-slate-200">Key Topics Outline</h4>
            {selectedSummary.summary_data.key_topics.map((topic, tIdx) => (
              <div key={tIdx} className="rounded-md border border-slate-800/60 bg-slate-950 p-5 space-y-4">
                <div>
                  <h5 className="text-md font-semibold text-white">{topic.name}</h5>
                  <p className="mt-1 text-sm text-slate-300">{topic.summary}</p>
                </div>

                {/* Core Concepts */}
                {topic.core_concepts && topic.core_concepts.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-blue-400">Core Concepts</p>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {topic.core_concepts.map((concept, cIdx) => (
                        <div key={cIdx} className="group relative rounded border border-slate-800/60 bg-slate-900 p-3 hover:border-blue-900/40 transition">
                          <p className="text-xs font-bold text-white">{concept.name}</p>
                          <p className="mt-1 text-xs text-slate-400 italic">"{concept.definition}"</p>
                          <p className="mt-1 text-xs text-slate-300">{concept.explanation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Formulas */}
                {topic.formulas && topic.formulas.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-blue-400">Formulas / Equations</p>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {topic.formulas.map((formula, fIdx) => (
                        <div key={fIdx} className="flex flex-col justify-between rounded border border-slate-800/60 bg-slate-900 p-3">
                          <code className="text-xs font-mono font-bold text-blue-400">{formula.equation}</code>
                          <p className="mt-1 text-[11px] text-slate-400">{formula.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Citations */}
                {topic.citations && topic.citations.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
                    <span>Sources:</span>
                    {topic.citations.map((cit, citIdx) => (
                      <span key={citIdx} className="rounded bg-slate-800 px-2 py-0.5 font-mono text-slate-400">
                        {cit}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* RENDER VIEW: DETAILED SYLLABUS COURSE MAP */}
      {selectedSyllabus && (
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-6 animate-fade-in space-y-6">
          <button
            onClick={() => setSelectedSyllabus(null)}
            className="text-xs font-semibold text-blue-400 hover:underline mb-2 block"
          >
            ← Back to Library
          </button>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800/60 pb-4 gap-3">
            <div>
              <span className="rounded bg-slate-800 px-2.5 py-1 text-[10px] font-bold text-blue-400 tracking-wider uppercase font-mono">
                {selectedSyllabus.subject_code || "COURSE"}
              </span>
              <h3 className="mt-2 text-2xl font-bold text-white">
                {selectedSyllabus.course_name || "Course Syllabus Map"}
              </h3>
            </div>
            <div className="flex gap-4">
              <div className="text-right">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Topics</p>
                <p className="text-lg font-bold text-white">{selectedSyllabus.topics.length}</p>
              </div>
              <div className="text-right">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Difficulty</p>
                <p className="text-lg font-bold text-blue-400 uppercase">{selectedSyllabus.estimated_difficulty || "Medium"}</p>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            { (Object.entries(
              selectedSyllabus.topics.reduce((acc: Record<string, any[]>, topic: any) => {
                const key = topic.unit_title || "General Unit";
                if (!acc[key]) acc[key] = [];
                acc[key].push(topic);
                return acc;
              }, {})
            ) as [string, any[]][]).map(([unitName, unitTopics]) => {
              const totalUnitHours = unitTopics.reduce((sum, t) => sum + t.estimated_hours, 0);

              return (
                <div key={unitName} className="rounded-md border border-slate-800/60 bg-slate-950 p-5 space-y-4">
                  <div className="flex justify-between items-center border-b border-slate-800/60 pb-3">
                    <h4 className="text-md font-bold text-white">{unitName}</h4>
                    <span className="text-xs text-slate-400 font-mono">
                      {totalUnitHours.toFixed(1)} Master Hours
                    </span>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    {unitTopics.map((topic) => (
                      <div
                        key={topic.id}
                        className="rounded border border-slate-800/60 bg-slate-900 p-4 space-y-3 hover:border-slate-800 transition"
                      >
                        <div className="flex justify-between items-start">
                          <h5 className="text-sm font-semibold text-white leading-5">{topic.topic_name}</h5>
                          <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                            Priority {topic.priority_rank}
                          </span>
                        </div>

                        <div className="flex flex-wrap gap-2 text-[10px] font-mono">
                          <span className={`px-2 py-0.5 rounded font-bold ${
                            topic.difficulty_level === "hard" ? "bg-red-500/10 text-red-400" :
                            topic.difficulty_level === "medium" ? "bg-yellow-500/10 text-yellow-400" :
                            "bg-green-500/10 text-green-400"
                          }`}>
                            {topic.difficulty_level.toUpperCase()}
                          </span>
                          <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
                            {topic.estimated_hours} hrs
                          </span>
                          <span className="bg-slate-800 text-blue-400 px-2 py-0.5 rounded">
                            Weight: {topic.importance_score.toFixed(1)}/10
                          </span>
                        </div>

                        {topic.dependencies && topic.dependencies.length > 0 && (
                          <div className="pt-2 border-t border-slate-800/60">
                            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1">Prerequisites</p>
                            <div className="flex flex-wrap gap-1">
                              {topic.dependencies.map((dep: string, depIdx: number) => (
                                <span key={depIdx} className="rounded bg-slate-800 px-1.5 py-0.5 text-[9px] font-mono text-slate-400">
                                  {dep}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* RENDER VIEW: INTERACTIVE QUIZ PLAYER */}
      {selectedQuiz && (
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-6 max-w-3xl mx-auto">
          <div className="mb-4 flex items-center justify-between">
            <button
              onClick={() => {
                setSelectedQuiz(null);
                handleRestartQuiz();
              }}
              className="text-xs font-semibold text-blue-400 hover:underline"
            >
              ← Back to Library
            </button>
            <span className="text-xs text-slate-400">
              Question {currentQuestionIdx + 1} of {selectedQuiz.questions.length}
            </span>
          </div>

          <h3 className="text-xl font-bold text-white">{selectedQuiz.title}</h3>

          {!isQuizComplete ? (
            <div className="mt-6 space-y-6">
              {/* Question Text */}
              <div className="rounded-md bg-slate-950 p-5 border border-slate-800/60">
                <p className="text-md text-white font-medium">
                  {selectedQuiz.questions[currentQuestionIdx].question_text}
                </p>
              </div>

              {/* Options */}
              <div className="space-y-3">
                {selectedQuiz.questions[currentQuestionIdx].options.map((option, idx) => {
                  const isSelected = selectedOptionIdx === idx;
                  const isCorrect = idx === selectedQuiz.questions[currentQuestionIdx].correct_answer_idx;

                  let cardStyle = "border-slate-800/60 bg-slate-950 text-slate-300 hover:bg-slate-800";
                  if (isSelected && !isAnswerChecked) {
                    cardStyle = "border-cyan-400 bg-blue-600/10 text-blue-400 text-slate-200";
                  } else if (isAnswerChecked) {
                    if (isCorrect) {
                      cardStyle = "border-green-500 bg-green-500/10 text-green-200";
                    } else if (isSelected) {
                      cardStyle = "border-red-500 bg-red-500/10 text-red-200";
                    } else {
                      cardStyle = "border-slate-800/60 bg-slate-950/10 text-slate-500 opacity-60";
                    }
                  }

                  return (
                    <button
                      key={idx}
                      onClick={() => handleSelectOption(idx)}
                      disabled={isAnswerChecked}
                      className={`w-full text-left rounded border p-4 text-sm font-semibold transition-all duration-200 flex items-center justify-between ${cardStyle}`}
                    >
                      <span>{option}</span>
                      {isAnswerChecked && isCorrect && <span className="text-green-400">✓</span>}
                      {isAnswerChecked && isSelected && !isCorrect && <span className="text-red-400">✗</span>}
                    </button>
                  );
                })}
              </div>

              {/* Explanation Box */}
              {isAnswerChecked && (
                <div className="rounded-md border border-slate-800/60 bg-slate-950 p-5 space-y-3 animate-fade-in">
                  <div>
                    <p className="text-xs uppercase tracking-wider font-bold text-blue-400">Explanation</p>
                    <p className="mt-1 text-sm text-slate-300">
                      {selectedQuiz.questions[currentQuestionIdx].explanation}
                    </p>
                  </div>
                  {selectedQuiz.questions[currentQuestionIdx].source_citation && (
                    <div className="pt-2 border-t border-slate-800/60">
                      <p className="text-[11px] text-slate-500">
                        Grounded Citation: <span className="font-mono text-slate-400">"{selectedQuiz.questions[currentQuestionIdx].source_citation}"</span>
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Actions Footer */}
              <div className="flex justify-end pt-4 border-t border-slate-800">
                {!isAnswerChecked ? (
                  <button
                    onClick={handleCheckAnswer}
                    disabled={selectedOptionIdx === null}
                    className="rounded-md bg-white hover:bg-slate-200 px-6 py-3 text-sm font-semibold text-slate-950 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Check Answer
                  </button>
                ) : (
                  <button
                    onClick={handleNextQuestion}
                    className="rounded-md bg-white hover:bg-slate-200 px-6 py-3 text-sm font-semibold text-slate-950 transition-all duration-200"
                  >
                    {currentQuestionIdx + 1 < selectedQuiz.questions.length ? "Next Question →" : "Finish Quiz"}
                  </button>
                )}
              </div>
            </div>
          ) : (
            /* Score Summary Screen */
            <div className="mt-10 flex flex-col items-center justify-center text-center space-y-6 bg-slate-950 p-8 rounded-lg border border-slate-800/60">
              <div className="text-6xl">🏆</div>
              <div>
                <h4 className="text-2xl font-bold text-white">Quiz Completed!</h4>
                <p className="text-sm text-slate-400 mt-1">Excellent practice. Spaced repetition improves retention.</p>
              </div>

              <div className="rounded-full h-32 w-32 border-4 border-cyan-400 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-white">{quizScore}</span>
                <span className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">score / {selectedQuiz.questions.length}</span>
              </div>

              <button
                onClick={handleRestartQuiz}
                className="rounded-md bg-slate-800 border border-slate-800 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                Retake Quiz
              </button>
            </div>
          )}
        </div>
      )}

      {/* RENDER TAB VIEW: DOCUMENTS */}
      {activeTab === "files" && !selectedSummary && !selectedQuiz && !selectedSyllabus && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {files.map((file) => {
            const hasSummary = summaries.some((s) => s.file_id === file.id);
            const hasQuizzes = quizzes.some((q) => q.file_id === file.id);

            return (
              <div key={file.id} className="rounded-md border border-slate-800 bg-slate-900 p-5 flex flex-col justify-between space-y-4 hover:border-white/20 transition">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-blue-400 uppercase">
                      {file.file_type.replace(".", "") || "File"}
                    </span>
                    <span className="text-[11px] text-slate-500">{formatSize(file.file_size)}</span>
                  </div>
                  <h4 className="mt-2 text-md font-bold text-white truncate" title={file.file_name}>
                    {file.file_name}
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Uploaded {new Date(file.uploaded_at).toLocaleDateString()}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-800/60 flex flex-col gap-2">
                  {hasSummary ? (
                    <button
                      onClick={() => setSelectedSummary(summaries.find((s) => s.file_id === file.id) || null)}
                      className="w-full text-center rounded bg-slate-900 border border-slate-800 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 hover:text-white transition-all duration-200"
                    >
                      Read Summary Guide
                    </button>
                  ) : (
                    <div className="text-center text-[10px] text-slate-500 italic py-1">
                      No summary. Ask AI in chat to summarize it.
                    </div>
                  )}

                  {hasQuizzes ? (
                    <button
                      onClick={() => {
                        const fileQuiz = quizzes.find((q) => q.file_id === file.id);
                        if (fileQuiz) setSelectedQuiz(fileQuiz);
                      }}
                      className="w-full text-center rounded bg-slate-900 border border-slate-800 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 hover:text-white transition-all duration-200"
                    >
                      Take Practice Quiz
                    </button>
                  ) : (
                    <div className="text-center text-[10px] text-slate-500 italic py-1">
                      No quizzes. Ask AI in chat to write a quiz.
                    </div>
                  )}

                  {syllabi[file.id] ? (
                    <button
                      onClick={() => setSelectedSyllabus(syllabi[file.id])}
                      className="w-full text-center rounded bg-slate-900 border border-slate-800 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 hover:text-white transition-all duration-200"
                    >
                      View Course Map
                    </button>
                  ) : (
                    <button
                      onClick={async () => {
                        setIsLoading(true);
                        try {
                          const resp = await fetch(`http://127.0.0.1:8000/syllabus/file/${file.id}/analyze`, {
                            method: "POST"
                          });
                          if (resp.ok) {
                            const data = await resp.json();
                            setSyllabi(prev => ({ ...prev, [file.id]: data }));
                            setSelectedSyllabus(data);
                          }
                        } catch (err) {
                          console.error("Failed to analyze syllabus:", err);
                        } finally {
                          setIsLoading(false);
                        }
                      }}
                      className="w-full text-center rounded bg-slate-900 border border-slate-800 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 hover:text-white transition-all duration-200"
                    >
                      Extract Course Syllabus
                    </button>
                  )}
                </div>
              </div>
            );
          })}

          {files.length === 0 && (
            <div className="col-span-full text-center py-16 text-slate-500 italic">
              No documents uploaded yet. Go to Chat to upload files.
            </div>
          )}
        </div>
      )}



      {/* RENDER TAB VIEW: QUIZZES LIST */}
      {activeTab === "quizzes" && !selectedSummary && !selectedQuiz && (
        <div className="grid gap-4 sm:grid-cols-2">
          {quizzes.map((quiz) => (
            <div
              key={quiz.id}
              onClick={() => setSelectedQuiz(quiz)}
              className="cursor-pointer rounded-md border border-slate-800 bg-slate-900 p-5 hover:border-cyan-400/40 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="rounded bg-blue-600/10 text-blue-400 px-2 py-0.5 text-[10px] font-bold text-blue-400">
                    Assessment
                  </span>
                  <span className="text-[11px] text-slate-500">{quiz.questions.length} questions</span>
                </div>
                <h4 className="mt-2 text-lg font-bold text-white">{quiz.title}</h4>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/60 text-[11px] text-slate-500 text-right">
                Generated {new Date(quiz.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}

          {quizzes.length === 0 && (
            <div className="col-span-full text-center py-16 text-slate-500 italic">
              No quizzes found. Upload a file and type "Write a quiz on force" in chat!
            </div>
          )}
        </div>
      )}
    </div>
  );
}
