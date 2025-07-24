import React, { useState, useRef, useImperativeHandle, forwardRef, useLayoutEffect } from 'react';
import { InputFormProps } from '../types';

// Define the ref type for the InputForm component
export interface InputFormRef {
  focus: () => void;
}

const InputForm = forwardRef<InputFormRef, InputFormProps>(({ value, onChange, onSend, isLoading, placeholder }, ref) => {
  const [inputValue, setInputValue] = useState<string>('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;

    if (ta.value === "") {
      ta.style.height = "";
    } else {
      ta.style.height = "auto";
      ta.style.height = `${ta.scrollHeight}px`;
    }
  }, [inputValue]);

  // Expose the focus method to parent components
  useImperativeHandle(ref, () => ({
    focus: () => {
      textareaRef.current?.focus();
    }
  }));

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSend(inputValue);
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>): void => {
    setInputValue(e.target.value);
  };

  return (
    <form className="p-4 md:p-5 border-t border-gray-200 bg-gray-50" onSubmit={handleSubmit}>
      <div className="flex gap-2 md:gap-3 items-end">
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={isLoading}
          rows={1}
          className="w-full min-h-[40px] md:min-h-[40px] max-h-[120px] resize-none overflow-y-hidden border border-gray-300 rounded-sm px-3 py-2 md:px-4 md:py-3 text-sm md:text-sm font-inherit leading-relaxed transition-colors duration-200 focus:outline-none focus:border-blue-500 focus:shadow-[0_0_0_2px_rgba(59,130,246,0.25)] disabled:bg-gray-200 disabled:text-gray-500 disabled:cursor-not-allowed"
        />
        <button
          type="submit"
          disabled={isLoading || !inputValue.trim()}
          className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white border-none rounded-full px-4 py-2 md:px-5 md:py-3 text-sm md:text-sm font-medium cursor-pointer transition-colors duration-200 min-w-[60px] md:min-w-[60px] h-[40px] md:h-[40px] flex items-center justify-center active:scale-95"
        >
          {isLoading ? (
            <span className="text-base">⏳</span>
          ) : (
            <span>Send</span>
          )}
        </button>
      </div>
    </form>
  );
});

export default InputForm;