import { useRef } from "react";
import { Loader2, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  formatDocument,
  getDocumentMaxLength,
  limitRawLength,
  parseDocument,
} from "@/lib/formatters";
import type { Document, DocumentType } from "@/types/domain";

interface DocumentFieldEditorProps {
  documents: Document[];
  setDocuments: React.Dispatch<React.SetStateAction<Document[]>>;
  documentErrors: Record<string, string>;
  setDocumentErrors: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  isLoadingDocs: boolean;
  isSubmitting: boolean;
}

const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  RG: "RG",
  CPF: "CPF",
  CNPJ: "CNPJ",
};

const EMPTY_DOCUMENT: Omit<Document, "_tempId" | "isDeleted"> = {
  document_type: "RG",
  document: "",
};

/**
 * Inline editor for a list of documents, shared by the RenterDialog and
 * the OwnerDialog. Manages the document rows internally and exposes a
 * `getDocuments()` callback so the parent can read the final list when
 * submitting.
 *
 * Props:
 * - documents: array of { id?, _tempId, document_type, document, isDeleted }
 * - setDocuments: the parent's state setter
 * - documentErrors: map keyed by id/_tempId → error message
 * - isLoadingDocs: whether documents are being fetched (edit mode)
 * - isSubmitting: whether the parent form is submitting
 */
export function DocumentFieldEditor({
  documents,
  setDocuments,
  documentErrors,
  setDocumentErrors,
  isLoadingDocs,
  isSubmitting,
}: DocumentFieldEditorProps) {
  // Per-instance counter for temp IDs; replaces the old module-level
  // `let documentTempId = 0` which was shared and unsafe.
  const tempIdRef = useRef(0);

  const visibleDocuments = documents.filter((d) => !d.isDeleted);

  function addDocument(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    event.stopPropagation();
    tempIdRef.current += 1;
    setDocuments((prev) => [
      ...prev,
      {
        ...EMPTY_DOCUMENT,
        _tempId: `temp-${tempIdRef.current}`,
        isDeleted: false,
      },
    ]);
  }

  function updateDocument(index: number, field: string, value: string) {
    setDocuments((prev) =>
      prev.map((doc, i) => {
        if (i !== index) return doc;
        if (field === "document") {
          return { ...doc, document: formatDocument(doc.document_type, value) };
        }
        if (field === "document_type") {
          const dt = value as DocumentType;
          return {
            ...doc,
            document_type: dt,
            document: formatDocument(dt, doc.document),
          };
        }
        return { ...doc, [field]: value };
      })
    );
    // Clear the error for this document row when the user edits it.
    const doc = documents[index];
    if (doc && setDocumentErrors) {
      const key = doc.id ?? doc._tempId;
      setDocumentErrors((prev) => ({ ...prev, [key!]: "" }));
    }
  }

  function removeDocument(index: number) {
    setDocuments((prev) =>
      prev.map((doc, i) => (i === index ? { ...doc, isDeleted: true } : doc))
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>Documentos</Label>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={addDocument}
          disabled={isSubmitting || isLoadingDocs}
        >
          <Plus className="mr-1 h-4 w-4" />
          Adicionar documento
        </Button>
      </div>

      {isLoadingDocs ? (
        <div className="flex items-center justify-center py-4 text-sm text-muted-foreground">
          <LoadingText />
        </div>
      ) : visibleDocuments.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Nenhum documento cadastrado.
        </p>
      ) : (
        <div className="space-y-2">
          {visibleDocuments.map((doc) => {
            const actualIndex = documents.findIndex((d) => d === doc);
            const docError = documentErrors[doc.id ?? doc._tempId!];
            const isExisting = typeof doc.id === "number";
            return (
              <div
                key={doc.id ?? doc._tempId}
                className="space-y-1"
              >
                <div className="flex items-start gap-2">
                  {isExisting ? (
                    <>
                      <div className="flex h-10 w-28 items-center rounded-md border bg-muted px-3 text-sm font-medium text-muted-foreground">
                        {DOCUMENT_TYPE_LABELS[doc.document_type]}
                      </div>
                      <div className="flex h-10 flex-1 items-center rounded-md border bg-muted px-3 text-sm text-muted-foreground">
                        {doc.document || (
                          <span className="italic">—</span>
                        )}
                      </div>
                    </>
                  ) : (
                    <>
                      <Select
                        value={doc.document_type}
                        onValueChange={(value) =>
                          updateDocument(actualIndex, "document_type", value)
                        }
                        disabled={isSubmitting}
                      >
                        <SelectTrigger className="w-28">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(DOCUMENT_TYPE_LABELS).map(
                            ([value, label]) => (
                              <SelectItem key={value} value={value}>
                                {label}
                              </SelectItem>
                            )
                          )}
                        </SelectContent>
                      </Select>
                      <Input
                        placeholder={
                          doc.document_type === "CNPJ"
                            ? "00.000.000/0000-00"
                            : doc.document_type === "CPF"
                              ? "000.000.000-00"
                              : "00.000.000-0"
                        }
                        value={doc.document}
                        onChange={(e) =>
                          updateDocument(actualIndex, "document", e.target.value)
                        }
                        onBeforeInput={limitRawLength(
                          parseDocument,
                          getDocumentMaxLength(doc.document_type)
                        ) as unknown as React.FormEventHandler<HTMLInputElement>}
                        disabled={isSubmitting}
                        aria-invalid={!!docError}
                      />
                    </>
                  )}
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-10 w-10 shrink-0 text-destructive hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => removeDocument(actualIndex)}
                    disabled={isSubmitting}
                  >
                    <Trash2 className="h-4 w-4" />
                    <span className="sr-only">Remover</span>
                  </Button>
                </div>
                {docError && (
                  <p className="text-xs text-destructive">{docError}</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function LoadingText() {
  return (
    <>
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      Carregando documentos...
    </>
  );
}
