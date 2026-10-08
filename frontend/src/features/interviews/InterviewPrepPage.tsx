/**
 * Interview Preparation Hub Page.
 * Stage 7: Interviews & Interview Preparation.
 */

import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ProgressBar } from "@/components/ui/ProgressBar";
import {
  ArrowLeft,
  BookOpen,
  CheckSquare,
  Building2,
  Users,
  HelpCircle,
  FileText,
  Save,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import { interviewService } from "@/services/interviewService";
import type {
  ChecklistItem,
  InterviewPreparationUpdateInput,
} from "@/types/interview.types";

export const InterviewPrepPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  // Local state for preparation fields
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [newChecklistText, setNewChecklistText] = useState("");
  const [companyResearch, setCompanyResearch] = useState("");
  const [roleResearch, setRoleResearch] = useState("");
  const [questionsToAsk, setQuestionsToAsk] = useState("");
  const [personalNotes, setPersonalNotes] = useState("");
  const [postInterviewNotes, setPostInterviewNotes] = useState("");

  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Query: Interview details
  const { data: interview, isLoading: isInterviewLoading } = useQuery({
    queryKey: ["interview", id],
    queryFn: () => interviewService.getInterview(id!),
    enabled: !!id,
  });

  // Query: Preparation data
  const { data: prepData, isLoading: isPrepLoading } = useQuery({
    queryKey: ["interview-prep", id],
    queryFn: () => interviewService.getPreparation(id!),
    enabled: !!id,
  });

  // Initialize local state when prepData loads
  useEffect(() => {
    if (prepData) {
      setChecklist(prepData.preparation_checklist || []);
      setCompanyResearch(prepData.company_research || "");
      setRoleResearch(prepData.role_research || "");
      setQuestionsToAsk(prepData.questions_to_ask || "");
      setPersonalNotes(prepData.personal_notes || "");
      setPostInterviewNotes(prepData.post_interview_notes || "");
    }
  }, [prepData]);

  // Mutation: Save Preparation
  const saveMutation = useMutation({
    mutationFn: (payload: InterviewPreparationUpdateInput) =>
      interviewService.updatePreparation(id!, payload),
    onSuccess: (updatedPrep) => {
      queryClient.setQueryData(["interview-prep", id], updatedPrep);
      queryClient.invalidateQueries({ queryKey: ["interview", id] });
      setSaveSuccess(true);
      setErrorMessage(null);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Failed to save preparation notes.";
      setErrorMessage(msg);
    },
  });

  const handleSave = () => {
    setErrorMessage(null);
    setSaveSuccess(false);

    saveMutation.mutate({
      preparation_checklist: checklist,
      company_research: companyResearch.trim() || null,
      role_research: roleResearch.trim() || null,
      questions_to_ask: questionsToAsk.trim() || null,
      personal_notes: personalNotes.trim() || null,
      post_interview_notes: postInterviewNotes.trim() || null,
    });
  };

  // Checklist handlers
  const handleToggleChecklist = (itemId: string) => {
    setChecklist((prev) =>
      prev.map((item) =>
        item.id === itemId ? { ...item, done: !item.done } : item
      )
    );
  };

  const handleAddChecklistItem = (e: React.FormEvent) => {
    e.preventDefault();
    const text = newChecklistText.trim();
    if (!text) return;

    const newItem: ChecklistItem = {
      id: "item-" + Date.now() + "-" + Math.random().toString(36).substr(2, 4),
      label: text,
      done: false,
    };

    setChecklist((prev) => [...prev, newItem]);
    setNewChecklistText("");
  };

  const handleDeleteChecklistItem = (itemId: string) => {
    setChecklist((prev) => prev.filter((item) => item.id !== itemId));
  };

  const totalItems = checklist.length;
  const completedItems = checklist.filter((item) => item.done).length;
  const completionPercent = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;

  if (isInterviewLoading || isPrepLoading) {
    return (
      <div className="space-y-6">
        <div className="h-6 bg-slate-200 rounded w-1/4 animate-pulse" />
        <Card className="p-8 space-y-4 animate-pulse bg-slate-50">
          <div className="h-8 bg-slate-200 rounded w-1/3" />
          <div className="h-4 bg-slate-200 rounded w-1/2" />
          <div className="h-40 bg-slate-200 rounded" />
        </Card>
      </div>
    );
  }

  const app = interview?.application;

  return (
    <div className="space-y-6">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center gap-3 text-sm text-slate-500">
        <Link
          to={`/interviews/${id}`}
          className="hover:text-blue-600 flex items-center gap-1 font-medium"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Interview Details
        </Link>
      </div>

      {/* Page Header */}
      <PageHeader
        title="Interview Preparation Hub"
        subtitle={`${interview?.round_name || "Interview Round"} • ${
          app?.company_name || interview?.company?.name || "Company"
        } (${app?.job_title || "Application"})`}
        actions={
          <div className="flex items-center gap-3">
            {saveSuccess && (
              <span className="text-xs font-semibold text-green-700 bg-green-50 px-2.5 py-1.5 rounded border border-green-200 flex items-center gap-1 animate-fade-in">
                <CheckCircle2 className="w-3.5 h-3.5" /> Notes Saved!
              </span>
            )}
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={saveMutation.isPending}
            >
              <Save className="w-4 h-4 mr-1.5" />
              {saveMutation.isPending ? "Saving..." : "Save Preparation Notes"}
            </Button>
          </div>
        }
      />

      {errorMessage && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols): Research, Questions, Personal Notes */}
        <div className="lg:col-span-2 space-y-6">
          {/* Company Research */}
          <Card>
            <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-600" />
              <div>
                <CardTitle className="text-base">Company & Product Research</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">
                  Business model, mission, market position, tech stack, recent launches, and company culture.
                </p>
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              <textarea
                rows={5}
                placeholder="Document company pillars, revenue model, products, engineering blog posts, engineering culture notes..."
                value={companyResearch}
                onChange={(e) => setCompanyResearch(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md p-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed font-sans"
              />
            </CardContent>
          </Card>

          {/* Role & Technical Competencies */}
          <Card>
            <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-600" />
              <div>
                <CardTitle className="text-base">Role & Technical Competencies</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">
                  Core competencies required, system architectures, key concepts, and algorithms to review.
                </p>
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              <textarea
                rows={5}
                placeholder="Review key distributed systems concepts, concurrency patterns, SQL query performance tuning, behavioral scenarios..."
                value={roleResearch}
                onChange={(e) => setRoleResearch(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md p-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed font-sans"
              />
            </CardContent>
          </Card>

          {/* Questions to Ask Interviewers */}
          <Card>
            <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center gap-2">
              <HelpCircle className="w-5 h-5 text-emerald-600" />
              <div>
                <CardTitle className="text-base">Questions to Ask the Interviewer</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">
                  High-signal questions regarding engineering roadmap, team friction points, and culture.
                </p>
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              <textarea
                rows={5}
                placeholder="1. What is the single biggest engineering bottleneck currently limiting the team's velocity?&#10;2. How are technical design trade-offs resolved across peer teams?&#10;3. What does success look like in the first 90 days for this role?"
                value={questionsToAsk}
                onChange={(e) => setQuestionsToAsk(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md p-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed font-sans"
              />
            </CardContent>
          </Card>

          {/* Personal Talking Points & STAR Stories */}
          <Card>
            <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center gap-2">
              <BookOpen className="w-5 h-5 text-amber-600" />
              <div>
                <CardTitle className="text-base">Talking Points & STAR Stories</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">
                  Key projects, metrics (e.g. 40% latency reduction), leadership examples, and challenge stories.
                </p>
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              <textarea
                rows={5}
                placeholder="Situation - Task - Action - Result stories to highlight during behavioral and technical deep dives..."
                value={personalNotes}
                onChange={(e) => setPersonalNotes(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md p-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed font-sans"
              />
            </CardContent>
          </Card>

          {/* Post-Interview Debrief */}
          <Card className="border-slate-300 bg-slate-50/50">
            <CardHeader className="pb-3 border-b border-slate-200 flex flex-row items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-slate-700" />
              <div>
                <CardTitle className="text-base">Post-Interview Debrief & Reflection</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">
                  Record immediate impressions right after the session: questions asked, answers given, areas for follow-up.
                </p>
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              <textarea
                rows={4}
                placeholder="Immediate session takeaways: What questions were asked? Where did I excel? What questions should I send in a thank-you note?"
                value={postInterviewNotes}
                onChange={(e) => setPostInterviewNotes(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md p-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed font-sans bg-white"
              />
            </CardContent>
          </Card>
        </div>

        {/* Right Column (1 col): Preparation Checklist */}
        <div className="space-y-6">
          <Card className="sticky top-6 border-slate-200">
            <CardHeader className="pb-3 border-b border-slate-100 space-y-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <CheckSquare className="w-4 h-4 text-blue-600" /> Checklist
                </CardTitle>
                <span className="text-xs font-bold text-slate-700">
                  {completedItems} of {totalItems} completed ({completionPercent}%)
                </span>
              </div>
              <ProgressBar value={completionPercent} />
            </CardHeader>

            <CardContent className="pt-4 space-y-4">
              {/* Add checklist item form */}
              <form onSubmit={handleAddChecklistItem} className="flex items-center gap-2">
                <Input
                  type="text"
                  placeholder="Add preparation item..."
                  value={newChecklistText}
                  onChange={(e) => setNewChecklistText(e.target.value)}
                  className="text-xs"
                />
                <Button type="submit" size="sm" variant="primary" className="shrink-0 text-xs">
                  <Plus className="w-3.5 h-3.5" />
                </Button>
              </form>

              {/* Checklist items list */}
              {checklist.length === 0 ? (
                <div className="text-center py-6 text-slate-400 text-xs italic">
                  No items in checklist yet. Add tasks like &quot;Review system design diagrams&quot; or &quot;Test webcam & mic&quot;.
                </div>
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                  {checklist.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between gap-2 p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors group"
                    >
                      <label className="flex items-center gap-2.5 cursor-pointer flex-1 min-w-0">
                        <input
                          type="checkbox"
                          checked={item.done}
                          onChange={() => handleToggleChecklist(item.id)}
                          className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 shrink-0"
                        />
                        <span
                          className={`text-xs select-none break-words ${
                            item.done
                              ? "line-through text-slate-400"
                              : "text-slate-800 font-medium"
                          }`}
                        >
                          {item.label}
                        </span>
                      </label>
                      <button
                        type="button"
                        onClick={() => handleDeleteChecklistItem(item.id)}
                        className="text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity p-1"
                        title="Delete item"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Save helper */}
              <div className="pt-3 border-t border-slate-100">
                <Button
                  variant="primary"
                  className="w-full text-xs"
                  onClick={handleSave}
                  disabled={saveMutation.isPending}
                >
                  <Save className="w-3.5 h-3.5 mr-1.5" />
                  {saveMutation.isPending ? "Saving..." : "Save Preparation Hub"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
