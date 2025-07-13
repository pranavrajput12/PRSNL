// Data processing & validation

import { v4 as uuidv4 } from 'uuid';
import TurndownService from 'turndown';
import Sanitizer from '../utils/sanitizer.js';

/**
 * Service for processing and validating conversation data
 */
class ConversationProcessor {
  /**
   * Turndown service instance for HTML to Markdown conversion
   * @private
   */
  static _turndownService = new TurndownService({
    headingStyle: 'atx',
    codeBlockStyle: 'fenced'
  });

  /**
   * Process and validate a conversation before sending to backend
   * @param {Object} conversation Raw conversation data from extractor
   * @returns {Object} Processed conversation ready for API submission
   * @throws {Error} If validation fails
   */
  static processConversation(conversation) {
    if (!conversation) {
      throw new Error('No conversation data provided');
    }

    // Validate required fields
    this._validateConversation(conversation);

    // Ensure conversation has a unique ID
    const conversationId = conversation.id || uuidv4();

    // Process messages: sanitize and convert to markdown
    const processedMessages = conversation.messages.map(message => {
      return this._processMessage(message);
    });

    // Filter out any empty messages
    const filteredMessages = processedMessages.filter(msg => 
      msg.content && (msg.content.text.trim() || msg.content.markdown.trim())
    );

    // Create final conversation object
    return {
      id: conversationId,
      title: Sanitizer.stripHtml(conversation.title || 'Untitled Conversation'),
      platform: conversation.platform,
      source_url: conversation.url || window.location.href,
      timestamp: conversation.fetchedAt || new Date().toISOString(),
      messages: filteredMessages
    };
  }

  /**
   * Process an individual message
   * @param {Object} message Message object
   * @returns {Object} Processed message
   * @private
   */
  static _processMessage(message) {
    // Ensure we have content objects
    const content = message.content || {};
    
    // Get sanitized text and HTML
    const sanitizedText = Sanitizer.stripHtml(content.text || '');
    const sanitizedHtml = Sanitizer.sanitize(content.html || '');
    
    // Convert HTML to Markdown
    const markdown = this._turndownService.turndown(sanitizedHtml || sanitizedText);
    
    return {
      id: message.id || uuidv4(),
      role: message.role,
      timestamp: message.timestamp || new Date().toISOString(),
      content: {
        text: sanitizedText,
        html: sanitizedHtml,
        markdown: markdown
      }
    };
  }

  /**
   * Validate conversation data
   * @param {Object} conversation Conversation to validate
   * @throws {Error} If validation fails
   * @private
   */
  static _validateConversation(conversation) {
    if (!conversation.platform) {
      throw new Error('Missing platform information');
    }

    if (!Array.isArray(conversation.messages) || conversation.messages.length === 0) {
      throw new Error('Conversation must contain at least one message');
    }

    // Check that messages have required fields
    conversation.messages.forEach((message, index) => {
      if (!message.role) {
        throw new Error(`Message at index ${index} is missing role`);
      }
      
      if (!message.content) {
        throw new Error(`Message at index ${index} is missing content`);
      }
    });
  }
}

export default ConversationProcessor;
