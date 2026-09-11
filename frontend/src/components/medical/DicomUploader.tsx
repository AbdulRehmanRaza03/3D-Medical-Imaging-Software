"use client";

import { useCallback, useRef, useState } from "react";

import { useDicom } from "@/hooks/useDicom";
import { IconAlert, IconCheck, IconSpinner, IconUpload } from "@/components/ui/icons";

export function DicomUploader() {
  const { upload } = useDicom();
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [name, setName] = useState("");

  const setAndValidate = useCallback((list: FileList | null) => {
    if (!list) return;
    const arr = Array.from(list);
    setFiles(arr);
  }, []);

  const onSubmit = async () => {
    if (files.length === 0) return;
    await upload.mutateAsync({ files, name: name || undefined });
    setFiles([]);
    setName("");
    if (inputRef.current) inputRef.current.value = "";
  };

  const totalSize = files.reduce((acc, f) => acc + f.size, 0);

  return (
    <div className="surface overflow-hidden">
      <div className="border-b border-slate-100 px-6 py-5">
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
            <IconUpload className="h-5 w-5" />
          </span>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Upload DICOM study</h2>
            <p className="mt-0.5 text-sm text-slate-500">
              Select one or more CT DICOM files. The system validates them, detects the
              series, orders the slices, and reconstructs a 3D volume automatically.
            </p>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div
          className={`group flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-8 py-12 text-center transition ${
            dragActive
              ? "border-brand-400 bg-brand-50"
              : "border-slate-200 bg-slate-50/50 hover:border-brand-300 hover:bg-brand-50/40"
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            setAndValidate(e.dataTransfer.files);
          }}
        >
          <span
            className={`flex h-14 w-14 items-center justify-center rounded-2xl transition ${
              dragActive
                ? "bg-brand-100 text-brand-600"
                : "bg-white text-slate-400 shadow-card group-hover:text-brand-500"
            }`}
          >
            <IconUpload className="h-7 w-7" />
          </span>

          {files.length === 0 ? (
            <>
              <p className="mt-4 text-sm font-medium text-slate-700">
                Drag &amp; drop DICOM files here
              </p>
              <p className="mt-1 text-xs text-slate-400">
                or{" "}
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  className="font-medium text-brand-600 hover:text-brand-700"
                >
                  browse files
                </button>{" "}
                from your computer
              </p>
            </>
          ) : (
            <>
              <p className="mt-4 text-sm font-medium text-slate-800">
                {files.length} file{files.length > 1 ? "s" : ""} selected
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {(totalSize / (1024 * 1024)).toFixed(1)} MB total
              </p>
            </>
          )}

          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".dcm,application/dicom,.ima"
            className="hidden"
            onChange={(e) => setAndValidate(e.target.files)}
          />
        </div>

        {/* Study name field */}
        <div className="mt-5">
          <label className="label">Study name <span className="font-normal text-slate-400">(optional)</span></label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Patient knee CT — de-identified"
            className="input mt-1.5"
          />
        </div>

        {/* Status feedback */}
        {upload.isError && (
          <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <IconAlert className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{(upload.error as Error).message}</span>
          </div>
        )}
        {upload.isSuccess && (
          <div className="mt-4 flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            <IconCheck className="mt-0.5 h-4 w-4 shrink-0" />
            <span>
              Study ingested successfully ({upload.data.series_detected} series detected).
            </span>
          </div>
        )}

        <div className="mt-5 flex items-center justify-end gap-2">
          {files.length > 0 && (
            <button onClick={() => setFiles([])} className="btn-ghost px-3 py-2">
              Clear
            </button>
          )}
          <button
            onClick={onSubmit}
            disabled={files.length === 0 || upload.isPending}
            className="btn-primary px-4 py-2"
          >
            {upload.isPending ? (
              <>
                <IconSpinner className="h-4 w-4" />
                Processing…
              </>
            ) : (
              <>
                <IconUpload className="h-4 w-4" />
                Upload &amp; ingest
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
